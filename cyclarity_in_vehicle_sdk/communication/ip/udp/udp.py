import select
import socket
from typing import Optional
from cyclarity_in_vehicle_sdk.communication.base.communicator_base import CommunicatorType
from cyclarity_in_vehicle_sdk.communication.ip.base.ip_communicator_base import IpConnectionlessCommunicatorBase, IpVersion
from pydantic import Field, IPvAnyAddress

SOCK_DATA_RECV_AMOUNT = 4096

## @brief A class used for UDP communication over IP networks.
# @param _socket A socket object used for the communication.
class UdpCommunicator(IpConnectionlessCommunicatorBase):
    _socket: socket.socket = None
    
    ## @brief Opens the socket and sets it up for UDP communication.
    # @return A boolean indicating if the socket was successfully opened.   
    def open(self) -> bool:
        if self.source_ip.version == 6:
            self._socket = socket.socket(
                socket.AF_INET6,
                socket.SOCK_DGRAM,
            )
        else:
            self._socket = socket.socket(
                socket.AF_INET,
                socket.SOCK_DGRAM,
            )

        self._socket.bind((self.source_ip.exploded, self.sport))
        self._socket.setblocking(0)

    ## @brief Closes the socket.
    # @return A boolean indicating if the socket was successfully closed.
    def close(self) -> bool:
        self._socket.close()

    ## @brief Sends data to the specified IP address and port.
    # @param data The data to be sent.
    # @param timeout The timeout for the send operation.
    # @return The number of bytes sent.
    def send(self, data: bytes, timeout: Optional[float] = None) -> int:
        self._socket.sendto(
            data,
            (self.destination_ip.exploded, self.dport),
        )

    ## @brief Sends data to a specific IP address.
    # @param target_ip The target IP address.
    # @param data The data to be sent.
    # @return The number of bytes sent.
    def send_to(self, target_ip: IPvAnyAddress, data: bytes) -> int:
        self._socket.sendto(
            data,
            (target_ip.exploded, self.dport),
        )

    ## @brief Receives data from the socket.
    # @param recv_timeout The timeout for the receive operation.
    # @param size The size of the data to be received.
    # @return The data received.
    def recv(self, recv_timeout: float = 0, size: int = SOCK_DATA_RECV_AMOUNT) -> bytes:
        recv_data = None
        ready = select.select([self._socket], [], [], recv_timeout)
        if ready[0]:
            recv_data = self._socket.recv(size)
        return recv_data
    
    ## @brief Receives data from a specific IP address and port.
    # @param size The size of the data to be received.
    # @param recv_timeout The timeout for the receive operation.
    # @return The data received and the sender's IP address.
    def receive_from(self, size: int = SOCK_DATA_RECV_AMOUNT, recv_timeout: int = 0) -> tuple[bytes, IPvAnyAddress]:
        recv_tuple: tuple[bytes, IPvAnyAddress] = (None, None)
        if recv_timeout > 0:
            select.select([self.socket], [], [], recv_timeout)
        try:
            recv_tuple = self._socket.recvfrom(size)
        except BlockingIOError:
            pass
        return recv_tuple

    ## @brief Returns the type of the communicator.
    # @return The type of the communicator.
    def get_type(self) -> CommunicatorType:
        return CommunicatorType.UDP
