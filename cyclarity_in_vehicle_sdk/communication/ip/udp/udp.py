import select
import socket
from typing import Optional
from cyclarity_in_vehicle_sdk.communication.base.communicator_base import CommunicatorType
from cyclarity_in_vehicle_sdk.communication.ip.base.ip_communicator_base import IpConnectionlessCommunicatorBase
from pydantic import IPvAnyAddress

SOCK_DATA_RECV_AMOUNT = 4096

class UdpCommunicator(IpConnectionlessCommunicatorBase):
    """A class used for UDP communication over IP networks.
    """
    _socket: socket.socket = None

    def open(self) -> bool:
        """Opens the socket.
        Returns:
            bool: A boolean indicating if the socket was successfully opened.
        """
        if self.source_ip.version == 6:
            self._socket = socket.socket(
                socket.AF_INET6,
                socket.SOCK_DGRAM,
            )
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._socket.bind((self.source_ip.exploded, self.sport, 0, 0))
        else:
            self._socket = socket.socket(
                socket.AF_INET,
                socket.SOCK_DGRAM,
            )
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._socket.bind((self.source_ip.exploded, self.sport))

        self._socket.setblocking(0)

    def close(self) -> bool:
        """Closes the socket.

        Returns:
            bool: A boolean indicating if the socket was successfully closed.
        """
        self._socket.close()

    def send(self, data: bytes, timeout: Optional[float] = None) -> int:
        """Sends data to the specified IP address and port.

        Args:
            data (bytes): data The data to be sent.
            timeout (Optional[float], optional): The timeout for the send operation.

        Returns:
            int: The number of bytes sent.
        """
        self._socket.sendto(
            data,
            (self.destination_ip.exploded, self.dport),
        )

    def send_to(self, target_ip: IPvAnyAddress, data: bytes) -> int:
        """Sends data to a specific IP address and port.

        Args:
            target_port (int): The target port.
            target_ip (IPvAnyAddress): The target IP address.
            data (bytes): The data to be sent.

        Returns:
            int: The number of bytes sent.
        """
        self._socket.sendto(
            data,
            (target_ip.exploded, self.dport),
        )

    def recv(self, recv_timeout: float = 0, size: int = SOCK_DATA_RECV_AMOUNT) -> bytes:
        """Receives data from the socket.

        Args:
            recv_timeout (float, optional): The timeout for the receive operation.
            size (int, optional): The size of the data to be received.

        Returns:
            bytes: The data received.
        """
        recv_data = None
        ready = select.select([self._socket], [], [], recv_timeout)
        if ready[0]:
            recv_data = self._socket.recv(size)
        return recv_data

    def receive_from(self, size: int = SOCK_DATA_RECV_AMOUNT, recv_timeout: int = 0) -> tuple[bytes, IPvAnyAddress]:
        """Receives data from the socket

        Args:
            size (int, optional): The size of the data to be received.
            recv_timeout (int, optional): The timeout for the receive operation.

        Returns:
            tuple[bytes, IPvAnyAddress]: The data received and the sender's IP address.
        """
        recv_tuple: tuple[bytes, IPvAnyAddress] = (None, None)
        if recv_timeout > 0:
            select.select([self.socket], [], [], recv_timeout)
        try:
            recv_tuple = self._socket.recvfrom(size)
        except BlockingIOError:
            pass
        return recv_tuple

    def get_type(self) -> CommunicatorType:
        return CommunicatorType.UDP
