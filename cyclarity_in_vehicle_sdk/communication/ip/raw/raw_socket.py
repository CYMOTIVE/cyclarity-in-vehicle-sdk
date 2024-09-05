import socket
import asyncio
from typing import Callable, Optional
from enum import Enum

from cyclarity_in_vehicle_sdk.communication.ip.base.raw_socket_base import RawSocketCommunicatorBase
from pydantic import Field
from py_pcapplusplus import RawSocket, Packet, IPv4Layer, IPv6Layer, LayerType

class IpVersion(str, Enum):
    IPv4 = "IPv4"
    IPv6 = "IPv6"

# This class was just partially tested, and not in use by runnables ATM, do not use blindly
class Layer2RawSocket(RawSocketCommunicatorBase):
    if_name: str = Field(description="Name of ethernet interface to work with. (e.g. eth0, eth1 etc...)")

    def open(self) -> bool:
        self.raw_socket: RawSocket = RawSocket(self.if_name)
        return True
    
    def close(self) -> bool:
        return True
    
    def send(self, packet: Packet) -> bool:
        if self.raw_socket:
            return self.raw_socket.send_packet(packet)

    def send_receive_packet(self, packet: Packet, is_answer: Callable[[Packet], bool], timeout: int = 2) -> Optional[Packet]:
        if self.raw_socket:
            found_packet: Packet = None
        
            async def find_packet(in_socket: RawSocket, timeout: int):
                nonlocal found_packet
                nonlocal is_answer
                sniffed_packets = in_socket.sniff(timeout=timeout)
                for sniffed_packet in sniffed_packets:
                    if is_answer(sniffed_packet):
                        found_packet = sniffed_packet
            
            loop = asyncio.new_event_loop()
            find_packet_task = loop.create_task(find_packet(self.raw_socket, timeout))
            self.send(packet)
            loop.run_until_complete(find_packet_task)
            return found_packet
    
    def receive(self, timeout: int) -> Optional[Packet]:
        if self.raw_socket:
            if timeout > 0:
                return self.raw_socket.receive_packet(blocking=False, timeout=timeout)
            else:
                return self.raw_socket.receive_packet()
            


class Layer3RawSocket(RawSocketCommunicatorBase):
    if_name: str = Field(description="Name of ethernet interface to work with. (e.g. eth0, eth1 etc...)")
    ip_version: IpVersion = Field(description="IP version. IPv4/IPv6")

    def open(self) -> bool:
        if self.ip_version == IpVersion.IPv4:
            self.out_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
            self.out_socket.setsockopt(socket.SOL_IP, socket.IP_HDRINCL, 1)
        else:
            self.out_socket = socket.socket(socket.AF_INET6, socket.SOCK_RAW, socket.IPPROTO_RAW)
        self.in_socket = RawSocket(self.if_name)
        return True

    def close(self) -> bool:
        self.out_socket.close()

    def send(self, packet: Packet) -> bool:
        # dst_addr:str
        ipv4_layer: IPv4Layer = packet.get_layer(LayerType.IPv4Layer)
        if not ipv4_layer:
            ipv6_layer: IPv6Layer = packet.get_layer(LayerType.IPv6Layer)
            if not ipv6_layer:
                self.logger.error("Can't send packets without destination address")
                return False
            else:
                dst_addr = ipv6_layer.dst_ip
        else:
            dst_addr = ipv4_layer.dst_ip

        return self.out_socket.sendto(bytes(packet), (dst_addr, 0))

    def send_receive_packet(self, packet: Packet, is_answer: Callable[[Packet], bool], timeout: float = 2) -> Optional[Packet]:
        found_packet = None
        
        async def find_packet(in_socket: RawSocket, timeout: float):
            nonlocal found_packet
            nonlocal is_answer
            sniffed_packets = in_socket.sniff(timeout=timeout)
            for sniffed_packet in sniffed_packets:
                if is_answer(sniffed_packet):
                    found_packet = sniffed_packet
        
        loop = asyncio.new_event_loop()
        find_packet_task = loop.create_task(find_packet(self.in_socket, timeout))
        self.send(packet)
        loop.run_until_complete(find_packet_task)
        return found_packet
                
    def receive(self, timeout: float = 2) -> Optional[Packet]:
        return self.in_socket.receive_packet(blocking=True, timeout=timeout)
    