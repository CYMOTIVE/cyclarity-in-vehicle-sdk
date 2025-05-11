import select
import socket
from typing import Optional
from types import TracebackType
from cyclarity_in_vehicle_sdk.communication.ip.base.ip_communicator_base import IpConnectionCommunicatorBase

from cyclarity_in_vehicle_sdk.communication.base.communicator_base import CommunicatorType

SOCK_DATA_RECV_AMOUNT = 4096

class TcpCommunicator(IpConnectionCommunicatorBase):
    """TCP Communicator. The class provides methods to open, close, send, receive data over a TCP connection.
    """
    _socket: socket.socket = None

    def open(self) -> bool:
        """Open the TCP socket for communication.

        Returns:
            bool: True if successful, False otherwise.
        """
        if self.source_ip.version == 6:
            self._socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._socket.bind((self.source_ip.exploded, self.sport, 0, 0))
        else:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._socket.bind((self.source_ip.exploded, self.sport))


        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        self._socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 1)
        self._socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 1)
        self._socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 1)
        return True

    def is_open(self) -> bool:
        """inform the state of the TCP socket

        Returns:
            bool: True if the socket is open and ready for send/receive operations, False otherwise.
        """
        try:
            data = self._socket.recv(16, socket.MSG_DONTWAIT | socket.MSG_PEEK)
            return bool(data)
        except BlockingIOError:
            return True  # socket is open and reading from it would block
        except ConnectionResetError:
            return False  # socket was closed for some other reason
        except TimeoutError:
            return True  # socket is open and reading from it would block
        except Exception as ex:
            self.logger.error(str(ex))
            return False

    def close(self) -> bool:
        """Close the TCP socket.

        Returns:
            bool: True if successful, False otherwise.
        """
        if self.is_open():
            self._socket.shutdown(socket.SHUT_RDWR)
        self._socket.close()
        return True

    def send(self, data: bytes, timeout: Optional[float] = None) -> int:
        """Sends data over the socket.

        Args:
            data (bytes): The bytes to send.
            timeout (Optional[float], optional): The optional timeout in seconds for sending data.

        Returns:
            int: The number of bytes sent, or 0 if an exception occurred.
        """
        try:
            return self._socket.send(data)
        except Exception as ex:
            self.logger.error(str(ex))

        return 0

    def recv(self, recv_timeout: float = 0, size: int = SOCK_DATA_RECV_AMOUNT) -> bytes:
        """Receives data from the socket.

        Args:
            recv_timeout (float, optional): The optional timeout in seconds for receiving data.. Defaults to 0.
            size (int, optional): The maximum amount of data to receive.

        Returns:
            bytes: The received bytes, or an empty bytes object if an exception occurred.
        """
        recv_data = bytes()
        if recv_timeout > 0:
            ready = select.select([self._socket], [], [], recv_timeout)
            if not ready[0]:
                return recv_data
        try:
            recv_data = self._socket.recv(size)
        except ConnectionResetError:
            pass
        return recv_data

    def __enter__(self):
        """Opens the socket and connects to the target when entering a context.

        Raises:
            RuntimeError: Raises a RuntimeError if opening the socket or connecting to the target fails.

        Returns:
            TcpCommunicator: The instance of the class.
        """
        if self.open() and self.connect():
            return self
        else:
            raise RuntimeError("Failed opening socket or connecting to target")

    def __exit__(self, exception_type: Optional[type[BaseException]], exception_value: Optional[BaseException], traceback: Optional[TracebackType]) -> bool:
        """ Closes the socket when exiting a context.

        Returns:
            bool: False to propagate exceptions if any occurred.
        """
        self.close()
        return False

    def connect(self) -> bool:
        """Connects the socket to the destination IP and port.

        Returns:
            bool: rue on successful completion.
        """
        self._socket.connect((self.destination_ip.exploded, self.dport))
        return True

    def get_type(self) -> CommunicatorType:
        return CommunicatorType.TCP
