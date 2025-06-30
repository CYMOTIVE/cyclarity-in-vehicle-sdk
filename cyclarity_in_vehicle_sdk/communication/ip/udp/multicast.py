import select
import socket
import struct
from typing import Optional
from cyclarity_in_vehicle_sdk.communication.ip.base.ip_communicator_base import IpConnectionlessCommunicatorBase
from pydantic import Field, IPvAnyAddress

from cyclarity_in_vehicle_sdk.communication.base.communicator_base import CommunicatorType

SOCK_DATA_RECV_AMOUNT = 4096

class MulticastCommunicator(IpConnectionlessCommunicatorBase):
    """A class used for multicast communication over IP networks.
    """
    interface_name: Optional[str] = Field(None, description="Network interface name - needed incase of IPv6 multicast")
    _socket: socket.socket = None

    def open(self) -> bool:
        """Opens the socket.
        Returns:
            bool: A boolean indicating if the socket was successfully opened.
        """
        if not self.destination_ip.is_multicast:
            raise RuntimeError(f"invalid multicast address provided: {str(self.destination_ip)}")
        
        if self.destination_ip.version != self.source_ip.version:
            raise RuntimeError(f"Mismatch in family type of the provided addresses\
                               , source: {str(self.source_ip)}, destination: {str(self.destination_ip)}")

        is_ipv6 = True if self.source_ip.version == 6 else False

        if is_ipv6 and not self.interface_name:
            raise RuntimeError("Using IPv6 for multicast but no interface name provided")

        if is_ipv6:
            self._socket = socket.socket(
                socket.AF_INET6,
                socket.SOCK_DGRAM,
            )
        else:
            self._socket = socket.socket(
                socket.AF_INET,
                socket.SOCK_DGRAM,
            )

        # allow reuse of address and port
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        if is_ipv6:
            self._socket.bind(("::", self.destination_port))
            interface_index = socket.if_nametoindex(self.interface_name)
            join_data = struct.pack("16sI", self.destination_ip.packed, interface_index)
            self._socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, join_data)
        else:
            self._socket.bind(("", self.destination_port))
            packed_local_addr = socket.inet_aton(str(self.source_ip))
            packed_multicast_addr = socket.inet_aton(str(self.destination_ip))
            mreq = struct.pack('4s4s', packed_multicast_addr, packed_local_addr)
            self._socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        self._socket.setblocking(False)
        return True

    def close(self) -> bool:
        """Closes the socket.

        Returns:
            bool: A boolean indicating if the socket was successfully closed.
        """
        self._socket.close()
        return True

    def send(self, data: bytes, timeout: Optional[float] = None) -> int:
        """Sends data to the multicast group.

        Args:
            data (bytes): data The data to be sent.
            timeout (Optional[float], optional): The timeout for the send operation.

        Returns:
            int: The number of bytes sent.
        """
        return self._socket.sendto(data, (str(self.destination_ip), self.destination_port))

    def recv(self, recv_timeout: float = 0, size: int = SOCK_DATA_RECV_AMOUNT) -> bytes:
        """Receives data from the multicast group.

        Args:
            recv_timeout (float, optional): The timeout for the receive operation.
            size (int, optional): The size of the data to be received.

        Returns:
            bytes: The data received.
        """
        recv_data: bytes = None
        if recv_timeout > 0:
            select.select([self._socket], [], [], recv_timeout)
        try:
            recv_data = self._socket.recv(size)
        except BlockingIOError:
            pass
        return recv_data

    def send_to(self, target_port: int, target_ip: IPvAnyAddress, data: bytes) -> int:
        """Sends data to a specific IP address and port.

        Args:
            target_port (int): The target port.
            target_ip (IPvAnyAddress): The target IP address.
            data (bytes): The data to be sent.

        Returns:
            int: The number of bytes sent.
        """
        return self._socket.sendto(data, (target_ip.exploded, target_port))

    def receive_from(self, size: int = SOCK_DATA_RECV_AMOUNT, recv_timeout: int = 0) -> tuple[bytes, IPvAnyAddress]:
        """Receives data from a specific IP address and port.

        Args:
            size (int, optional): The size of the data to be received.
            recv_timeout (int, optional): The timeout for the receive operation.

        Returns:
            tuple[bytes, IPvAnyAddress]: The data received and the sender's IP address.
        """
        recv_tuple: tuple[bytes, IPvAnyAddress] = (None, None)
        if recv_timeout > 0:
            select.select([self._socket], [], [], recv_timeout)
        try:
            recv_tuple = self._socket.recvfrom(size)
        except BlockingIOError:
            pass
        return recv_tuple

    def get_type(self) -> CommunicatorType:
        return CommunicatorType.MULTICAST
