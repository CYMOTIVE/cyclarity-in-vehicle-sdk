from ipaddress import ip_address
import select
import socket
import time
from typing import Optional
from types import TracebackType
from cyclarity_in_vehicle_sdk.communication.ip.base.ip_communicator_base import IpConnectionCommunicatorBase, IpVersion
from pydantic import Field, IPvAnyAddress, model_validator

from cyclarity_in_vehicle_sdk.communication.base.communicator_base import CommunicatorType

SOCK_DATA_RECV_AMOUNT = 4096

## @class TcpCommunicator
#  @brief This class provides a TCP implementation of the IpConnectionCommunicatorBase.
#  @details The class provides methods to open, close, send, receive data over a TCP connection.
class TcpCommunicator(IpConnectionCommunicatorBase):
    ## The TCP socket used for communication.
    _socket: socket.socket = None

    ## @fn open
    #  @brief Opens a TCP socket for communication.
    #  @details Sets socket options and binds the socket to the source IP and port.
    #  @return True on successful completion.
    def open(self) -> bool:
        if self.source_ip.version == 6:
            self._socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        else:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind((self.source_ip.exploded, self.sport))

        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        self._socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 1)
        self._socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 1)
        self._socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 1)
        return True
    
    ## @fn is_open
    #  @brief Checks if the socket is open.
    #  @details Attempts to receive data from the socket without blocking. 
    #           Returns True if data is received or if the operation would block, implying the socket is open.
    #           Returns False if the connection was reset or any other exception occurs.
    #  @return True if the socket is open, False otherwise.
    def is_open(self) -> bool:
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
        
    ## @fn close
    #  @brief Closes the socket if it is open.
    #  @return True on successful completion.
    def close(self) -> bool:
        if self.is_open():
            self._socket.shutdown(socket.SHUT_RDWR)
        self._socket.close()
        return True
    
    ## @fn send
    #  @brief Sends data over the socket.
    #  @param data The bytes to send.
    #  @param timeout The optional timeout for sending data.
    #  @return The number of bytes sent, or 0 if an exception occurred.
    def send(self, data: bytes, timeout: Optional[float] = None) -> int:
        try:
            return self._socket.send(data)
        except Exception as ex:
            self.logger.error(str(ex))

        return 0

    ## @fn recv
    #  @brief Receives data from the socket.
    #  @param recv_timeout The optional timeout for receiving data.
    #  @param size The maximum amount of data to receive.
    #  @return The received bytes, or an empty bytes object if an exception occurred.
    def recv(self, recv_timeout: float = 0, size: int = SOCK_DATA_RECV_AMOUNT) -> bytes:
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
    
    ## @fn __enter__
    #  @brief Opens the socket and connects to the target when entering a context.
    #  @return The instance of the class.
    #  @exception Raises a RuntimeError if opening the socket or connecting to the target fails.
    def __enter__(self):
        if self.open() and self.connect():
            return self
        else:
            raise RuntimeError("Failed opening socket or connecting to target")
    
    ## @fn __exit__
    #  @brief Closes the socket when exiting a context.
    #  @return False to propagate exceptions if any occurred.    
    def __exit__(self, exception_type: Optional[type[BaseException]], exception_value: Optional[BaseException], traceback: Optional[TracebackType]) -> bool:
        self.close()
        return False
    
    ## @fn connect
    #  @brief Connects the socket to the destination IP and port.
    #  @return True on successful completion.
    def connect(self):
        self._socket.connect((self.destination_ip.exploded, self.dport))
        return True

    ## @fn get_type
    #  @brief Returns the type of the communicator.
    #  @return CommunicatorType.TCP
    def get_type(self) -> CommunicatorType:
        return CommunicatorType.TCP
