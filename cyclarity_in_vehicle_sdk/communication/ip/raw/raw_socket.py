import socket
import asyncio
from typing import Callable, Sequence
import time

from cyclarity_in_vehicle_sdk.communication.ip.base.ip_communicator_base import IpVersion
from cyclarity_in_vehicle_sdk.communication.ip.base.raw_socket_base import RawSocketCommunicatorBase
from pydantic import Field
from py_pcapplusplus import RawSocket, Packet, IPv4Layer, IPv6Layer, LayerType


class Layer2RawSocket(RawSocketCommunicatorBase):
    """This class handles layer 2 raw socket communication.
    """
    if_name: str = Field(description="Name of ethernet interface to work with. (e.g. eth0, eth1 etc...)")
    _raw_socket: RawSocket | None = None

    def open(self) -> bool:
        """Open the raw socket for communication.

        Returns:
            bool: True if successful, False otherwise.
        """
        self._raw_socket: RawSocket = RawSocket(self.if_name)
        return True

    def close(self) -> bool:
        """Close the raw socket.

        Returns:
            bool: True if successful, False otherwise.
        """
        self._raw_socket = None
        return True

    def is_open(self) -> bool:
        """Check if the raw socket is open.

        Returns:
            bool: True if the socket is open, False otherwise.
        """
        return self._raw_socket is not None

    def send_packet(self, packet: Packet) -> bool:
        """Send a packet over the raw socket.

        Args:
            packet (Packet): The Packet to be sent.

        Returns:
            bool: True if the packet was sent successfully, False otherwise.
        """
        if self._raw_socket:
            return self._raw_socket.send_packet(packet)
        else:
            self.logger.error("Attempting to send a packet without openning the socket.")
            return False

    def send_packets(self, packets: Sequence[Packet]) -> bool:
        """Send multiple packets over the raw socket.

        Args:
            packets (Sequence[Packet]): The list of Packets to be sent.

        Returns:
            bool: True if the packets were sent successfully, False otherwise.
        """
        if self._raw_socket:
            return self._raw_socket.send_packets(packets)
        else:
            self.logger.error("Attempting to send packets without openning the socket.")
            return False

    def send_receive_packet(self, packet: Packet | Sequence[Packet] | None, is_answer: Callable[[Packet], bool], timeout: float = 2) -> Packet | None:
        """send packet or a sequence of packets and read an answer
        The answer is one packet that satisfy the "is_answer" callback provided.

        Note: This function uses the implementation of 'send_receive_packets', 
        Optionally override this function to have a better implementation (stop after the first valid packet arrives).

        Args:
            packet (Packet | Sequence[Packet] | None): the packet/packets to send. None to skip the sending operation.
            is_answer (Callable[[Packet], bool]): callback that receives a packet and returns True if this packet is the answer to sent one
            timeout (int): timeout for the operation

        Returns:
            Packet | None: The first packet that satisfy the "is_answer" callback, None if not found.
        """
        found_packets = self._send_receive_packets(packet, is_answer, timeout, max_answers=1)
        if found_packets:
            return found_packets[0] # Get first valid answer
        else:
            return None

    def send_receive_packets(self, packet: Packet | Sequence[Packet] | None, is_answer: Callable[[Packet], bool], timeout: float = 2) -> list[Packet]:
        """send packet or a sequence of packets and read a multiple packets answer
        The answer is a list of packets that satisfy the "is_answer" callback provided.

        Args:
            packet (Packet | Sequence[Packet] | None): the packet/packets to send. None to skip the sending operation.
            is_answer (Callable[[Packet], bool]): callback that receives a packet and returns True if this packet is the answer to sent one
            timeout (int): timeout for the operation

        Returns:
            list[Packet]: All packets received that satisfy the "is_answer" callback.
        """ 
        return self._send_receive_packets(packet, is_answer, timeout)

    def _send_receive_packets(self, packet: Packet | Sequence[Packet] | None, is_answer: Callable[[Packet], bool], timeout: float, max_answers=0) -> list[Packet]:
        if self._raw_socket:
            found_packets: list[Packet] = []

            async def find_packet(in_socket: RawSocket, timeout: int):
                nonlocal found_packets
                nonlocal is_answer
                time_spent = 0
                start_time = time.time()
                while time_spent < timeout:
                    packet = in_socket.receive_packet(timeout=timeout-time_spent)
                    if not packet:
                        break
                    if is_answer(packet):
                        found_packets.append(packet)
                        if max_answers and max_answers <= len(found_packets):
                            break
                    time_spent = time.time()-start_time
            
            loop = asyncio.new_event_loop()
            find_packet_task = loop.create_task(find_packet(self._raw_socket, timeout))
            if packet:
                self.send(packet)
            loop.run_until_complete(find_packet_task)
            return found_packets
        else:
            self.logger.error("Attempting to send packets without openning the socket.")
            raise Exception("Attempt transmitting over a closed Layer2 Raw Socket.")

    def receive(self, timeout: float = 2) -> Packet | None:
        """read a single packet from the socket

        Args:
            timeout (float): timeout in seconds for the operation, 0 for blocking receive.

        Returns:
            Packet | None: the read packet, None if timeout reached.
        """
        if self._raw_socket:
            if timeout > 0:
                return self._raw_socket.receive_packet(blocking=False, timeout=timeout)
            else:
                return self._raw_socket.receive_packet()
        else:
            self.logger.error("Attempting to receive packets without openning the socket.")
            raise Exception("Attempt to read from a closed Layer2 Raw Socket.")

    def receive_answer(self, is_answer: Callable[[Packet], bool], timeout: float = 2) -> Packet | None:
        """sniff communication and return a packet that satisfy the "is_answer" callback.

        Args:
            (Callable[[Packet], bool]): A callback that receives a packet and returns True if this packet is the answer looking for.
            timeout (float): The duration of the sniffing to locate the answer packet.

        Returns:
            Packet | None: The first packet that satisfy the "is_answer" callback, None if not found.
        """
        return self.send_receive_packet(None, is_answer, timeout)
    
    def receive_answers(self, is_answer: Callable[[Packet], bool], timeout: float = 2) -> list[Packet]:
        """Read a multiple packets and returns all packets that satisfy the "is_answer" callback provided.

        Args:
            is_answer (Callable[[Packet], bool]): A callback that receives a packet and returns True if this packet is the answer looking for.
            timeout (int): The duration of the sniffing to locate the answer packets.

        Returns:
            list[Packet]: All packets received that satisfy the "is_answer" callback.
        """ 
        return self.send_receive_packets(None, is_answer, timeout)


class Layer3RawSocket(RawSocketCommunicatorBase):
    """Layer 3 raw socket for communicator
    """
    if_name: str = Field(description="Name of ethernet interface to work with. (e.g. eth0, eth1 etc...)")
    ip_version: IpVersion = Field(description="IP version. IPv4/IPv6")
    _in_socket: RawSocket | None = None
    _out_socket: socket.socket | None = None

    def open(self) -> bool:
        """Open the raw socket for communication.

        Returns:
            bool: True if successful, False otherwise.
        """
        if self.ip_version == IpVersion.IPv4:
            self._out_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
            self._out_socket.setsockopt(socket.SOL_IP, socket.IP_HDRINCL, 1)
        elif self.ip_version == IpVersion.IPv6:
            self._out_socket = socket.socket(socket.AF_INET6, socket.SOCK_RAW, socket.IPPROTO_RAW)
        else:
            self.logger.error(f"Unexpected ip version {self.ip_version} set as type.")
            return False
        
        self._out_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, self.if_name.encode())
        self._in_socket = RawSocket(self.if_name)
        return True

    def close(self) -> bool:
        """Close the raw socket.

        Returns:
            bool: True if successful, False otherwise.
        """
        self._in_socket = None
        self._out_socket.close()
        return True

    def is_open(self) -> bool:
        """inform the state of the raw socket

        Returns:
            bool: True if the socket is open and ready for send/receive operations, False otherwise.
        """
        return self._in_socket is not None

    def send_packet(self, packet: Packet) -> bool:
        """send a packet to the raw socket

        Args:
            packet (Packet): packet to send.

        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.is_open():
            self.logger.error("Attempt sending packet to a closed socket.")
            return False
        
        if self.ip_version == IpVersion.IPv4:
            ipv4_layer: IPv4Layer = packet.get_layer(LayerType.IPv4Layer)
            if ipv4_layer:
                dst_addr = (ipv4_layer.dst_ip, 0)
            else:
                self.logger.error("Attempt transmittion of non ipv4 packet")
                self.logger.debug(f"packet = {packet}")
                return False
        elif self.ip_version == IpVersion.IPv6:
            ipv6_layer: IPv6Layer = packet.get_layer(LayerType.IPv6Layer)
            if ipv6_layer:
                dst_addr = (ipv6_layer.dst_ip, 0, 0, 0)
            else:
                self.logger.error("Attempt transmittion of non ipv4 packet")
                self.logger.debug(f"packet = {packet}")
                return False
        else:
            self.logger.error(f"Unexpected ip version {self.ip_version} set as type.")
            return False
        
        return self._out_socket.sendto(bytes(packet), dst_addr)


    def send_receive_packets(self, packet: Packet | Sequence[Packet] | None, is_answer: Callable[[Packet], bool], timeout: float) -> list[Packet]:
        """send packet or a sequence of packets and read a multiple packets answer
        The answer is a list of packets that satisfy the "is_answer" callback provided.

        Args:
            packet (Packet | Sequence[Packet] | None): the packet/packets to send. None to skip the sending operation.
            is_answer (Callable[[Packet], bool]): callback that receives a packet and returns True if this packet is the answer to sent one
            timeout (int): timeout for the operation

        Returns:
            list[Packet]: All packets received that satisfy the "is_answer" callback.
        """ 
        found_packet: list[Packet] = []
        
        async def find_packet(in_socket: RawSocket, timeout: float):
            nonlocal found_packet
            nonlocal is_answer
            sniffed_packets = in_socket.sniff(timeout=timeout)
            for sniffed_packet in sniffed_packets:
                if is_answer(sniffed_packet):
                    found_packet.append(sniffed_packet)
        
        loop = asyncio.new_event_loop()
        find_packet_task = loop.create_task(find_packet(self._in_socket, timeout))
        self.send(packet)
        loop.run_until_complete(find_packet_task)
        return found_packet

    def receive(self, timeout: float = 2) -> Packet | None:
        """read a single packet from the socket

        Args:
            timeout (float): timeout in seconds for the operation, 0 for blocking receive.

        Returns:
            Packet | None: the read packet, None if timeout reached.
        """
        if self._in_socket is None:
            self.logger.error("Attempt to read from a closed socket.")
            return None
        
        return self._in_socket.receive_packet(blocking=True, timeout=timeout)
    