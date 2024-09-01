import select
import socket
from typing import Optional
from types import TracebackType
from pydantic import Field, IPvAnyAddress

from cyclarity_in_vehicle_sdk.communication.base.communicator_base import CommunicatorType, ConnectionCommunicatorBase

SOCK_DATA_RECV_AMOUNT = 4096

class TcpCommunicator(ConnectionCommunicatorBase):
    sport: int = Field(None, description="Source port.")
    dport: int = Field(None, description="Destination port.")
    source_ip: IPvAnyAddress = Field(None, description="Source IP.")
    destination_ip: IPvAnyAddress = Field(None, description="Destination IP.")

    def open(self) -> bool:
        if self.source_ip.version == 6:
            self.socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        else:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.source_ip.exploded, self.sport))
        return True
    
    def is_open(self) -> bool:
        try:
            self.socket.recv(16, socket.MSG_DONTWAIT | socket.MSG_PEEK)
            return True
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
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()
        return True
    
    def send(self, data: bytes, timeout: Optional[float] = None) -> int:
        try:
            return self.socket.send(data)
        except Exception as ex:
            self.logger.error(str(ex))

        return 0

    def recv(self, recv_timeout: float = 0 , size: int = SOCK_DATA_RECV_AMOUNT) -> bytes:
        recv_data = bytes()
        if recv_timeout > 0:
            ready = select.select([self.socket], [], [], recv_timeout)
            if not ready[0]:
                return recv_data
        try:
            recv_data = self.socket.recv(size)
        except ConnectionResetError:
            pass
        return recv_data
    
    def __enter__(self):
        if self.open() and self.connect():
            return self
        else:
            raise RuntimeError("Failed opening socket or connecting to target")
        
    def __exit__(self, exception_type: Optional[type[BaseException]], exception_value: Optional[BaseException], traceback: Optional[TracebackType]) -> bool:
        self.close()
        return False
    
    def connect(self):
        self.socket.connect((self.destination_ip.exploded, self.dport))
        return True
    
    def get_type(self) -> CommunicatorType:
        return CommunicatorType.TCP
    