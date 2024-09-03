from abc import abstractmethod
from typing import Optional
from enum import Enum, auto
from cyclarity_sdk.expert_builder.runnable.runnable import ParsableModel
from pydantic import IPvAnyAddress

class CommunicatorType(Enum):
    UDP = auto()
    TCP = auto()
    ISOTP = auto()
    DOIP = auto()


class CommunicatorBase(ParsableModel):
    """base class for communicators
    """
    @abstractmethod
    def send(self, data: bytes, timeout: Optional[float] = None) -> int:
        """sends bytes over the communication layer

        Args:
            data (bytes): data to send in bytes format
            timeout (Optional[float]): timeout in seconds for send operation. defaults to None

        Returns:
            int: amount of bytes sent
        """
        raise NotImplementedError
    
    @abstractmethod
    def recv(self, recv_timeout: float, size: int) -> bytes:
        """receive data over the communication layer

        Args:
            recv_timeout (float): timeout in seconds for the operation
            size (int): amount of bytes to read

        Returns:
            bytes: the received bytes
        """
        raise NotImplementedError
    
    @abstractmethod
    def open(self) -> bool:
        """open the communicator
        """
        raise NotImplementedError
    
    @abstractmethod
    def close(self) -> bool:
        """close the communication
        """
        raise NotImplementedError
    
    @abstractmethod
    def get_type(self) -> CommunicatorType:
        """get the communicator type

        Returns:
            CommunicatorType: enum type of the communicator
        """
        raise NotImplementedError

class ConnectionCommunicatorBase(CommunicatorBase):
    """base class for communicators that require connection
    """
    @abstractmethod
    def connect(self) -> bool:
        """connect the communicator

        Returns:
            bool: True id connection succeeded False otherwise
        """
        raise NotImplementedError
    
    @abstractmethod
    def is_open(self) -> bool:
        raise NotImplementedError
    
class ConnectionlessCommunicatorBase(CommunicatorBase):
    """base class for communicators that are connection-less
    """
    @abstractmethod
    def send_to(self, target_ip: IPvAnyAddress, data: bytes) -> int:
        """send data to a destination

        Args:
            target_ip (IPvAnyAddress): the IP of the destination to send to
            data (bytes): the bytes to send

        Returns:
            int: amount of bytes sent
        """
        raise NotImplementedError
    
    @abstractmethod
    def receive_from(self, size: int) -> tuple[bytes, IPvAnyAddress]:
        """receive data from communicator and get the source address

        Args:
            size (int): amount of bytes to read

        Returns:
            tuple[bytes, IPvAnyAddress]: the received data in bytes, and the IP of the sender
        """
        raise NotImplementedError
    