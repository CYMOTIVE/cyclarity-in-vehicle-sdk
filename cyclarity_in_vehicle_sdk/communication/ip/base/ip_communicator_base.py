from abc import abstractmethod
from enum import Enum
from pydantic import IPvAnyAddress
from cyclarity_in_vehicle_sdk.communication.base.communicator_base import CommunicatorBase

class IpVersion(str, Enum):
    IPv4 = "IPv4"
    IPv6 = "IPv6"

class IpCommunicatorBase(CommunicatorBase):
    @abstractmethod
    def ip_version(self) -> IpVersion:
        raise NotImplementedError


class IpConnectionCommunicatorBase(IpCommunicatorBase):
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
    
class IpConnectionlessCommunicatorBase(IpCommunicatorBase):
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
    def receive_from(self, size: int, recv_timeout: int) -> tuple[bytes, IPvAnyAddress]:
        """receive data from communicator and get the source address

        Args:
            size (int): amount of bytes to read
            recv_timeout (float): timeout in seconds for the operation

        Returns:
            tuple[bytes, IPvAnyAddress]: the received data in bytes, and the IP of the sender
        """
        raise NotImplementedError