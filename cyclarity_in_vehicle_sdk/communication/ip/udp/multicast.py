import select
import socket
import struct
from typing import Optional
from cyclarity_in_vehicle_sdk.communication.ip.base.ip_communicator_base import IpConnectionlessCommunicatorBase, IpVersion
from pydantic import Field, IPvAnyAddress

from cyclarity_in_vehicle_sdk.communication.base.communicator_base import CommunicatorType

SOCK_DATA_RECV_AMOUNT = 4096

# This class was just partially tested, and not in use by runnables ATM, do not use blindly
## @brief A class used for multicast communication over IP networks.
# @param interface_name The network interface name - needed in case of IPv6 multicast
# @param _socket A socket object used for the communication
class MulticastCommunicator(IpConnectionlessCommunicatorBase):
    interface_name: Optional[str] = Field(None, description="Network interface name - needed incase of IPv6 multicast")
    _socket: socket.socket = None

    ## @brief Opens the socket and sets it up for multicast communication.
    # @return A boolean indicating if the socket was successfully opened.
    def open(self) -> bool:
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
            self._socket.bind((str(self.destination_ip), 0))
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
    
    ## @brief Closes the socket.
    # @return A boolean indicating if the socket was successfully closed.
    def close(self) -> bool:
        self._socket.close()
        return True
    
    ## @brief Sends data to the multicast group.
    # @param data The data to be sent.
    # @param timeout The timeout for the send operation.
    # @return The number of bytes sent.
    def send(self, data: bytes, timeout: Optional[float] = None) -> int:
        return self._socket.sendto(data, (str(self.destination_ip), self.dport))
    
    ## @brief Receives data from the multicast group.
    # @param recv_timeout The timeout for the receive operation.
    # @param size The size of the data to be received.
    # @return The data received.
    def recv(self, recv_timeout: float = 0, size: int = SOCK_DATA_RECV_AMOUNT) -> bytes:
        recv_data: bytes = None
        if recv_timeout > 0:
            select.select([self._socket], [], [], recv_timeout)
        try:
            recv_data = self._socket.recv(size)
        except BlockingIOError:
            pass
        return recv_data
    
    ## @brief Sends data to a specific IP address and port.
    # @param target_port The target port.
    # @param target_ip The target IP address.
    # @param data The data to be sent.
    # @return The number of bytes sent.
    def send_to(self, target_port: int, target_ip: IPvAnyAddress, data: bytes) -> int:
        return self._socket.sendto(data, (target_ip.exploded, target_port))

    ## @brief Receives data from a specific IP address and port.
    # @param size The size of the data to be received.
    # @param recv_timeout The timeout for the receive operation.
    # @return The data received and the sender's IP address.
    def receive_from(self, size: int = SOCK_DATA_RECV_AMOUNT, recv_timeout: int = 0) -> tuple[bytes, IPvAnyAddress]:
        recv_tuple: tuple[bytes, IPvAnyAddress] = (None, None)
        if recv_timeout > 0:
            select.select([self._socket], [], [], recv_timeout)
        try:
            recv_tuple = self._socket.recvfrom(size)
        except BlockingIOError:
            pass
        return recv_tuple

    ## @brief Returns the type of the communicator.
    # @return The type of the communicator.
    def get_type(self) -> CommunicatorType:
        return CommunicatorType.MULTICAST
