from abc import abstractmethod
from enum import Enum
from pydantic import Field, IPvAnyAddress
from cyclarity_in_vehicle_sdk.communication.base.communicator_base import CommunicatorBase

## @brief Enum for IP version.
class IpVersion(str, Enum):
    IPv4 = "IPv4"
    IPv6 = "IPv6"

## @brief Base class for IP protocol communicators.
class IpCommunicatorBase(CommunicatorBase):

    sport: int = Field(description="Source port.")  # Source port
    source_ip: IPvAnyAddress = Field(description="Source IP.")  # Source IP
    dport: int = Field(description="Destination port.")  # Destination port
    destination_ip: IPvAnyAddress = Field(description="Destination IP.")  # Destination IP

    ## @brief Property to get source IP.
    @property
    def source_ip(self) -> IPvAnyAddress:
        return self.source_ip
    
    ## @brief Property to get destination IP.
    @property
    def destination_ip(self) -> IPvAnyAddress:
        return self.destination_ip

    ## @brief Property to get source port.
    @property
    def source_port(self) -> int:
        return self.sport

    ## @brief Property to get destination port.
    @property
    def destination_port(self) -> int:
        return self.dport


## @brief Base class for communicators that require connection.
class IpConnectionCommunicatorBase(IpCommunicatorBase):

    ## @brief Method to connect the communicator.
    #  @return True if connection succeeded, False otherwise.
    @abstractmethod
    def connect(self) -> bool:
        raise NotImplementedError

    ## @brief Method to check if communicator is open.
    #  @return Bool indicating if communicator is open.
    @abstractmethod
    def is_open(self) -> bool:
        raise NotImplementedError


## @brief Base class for communicators that are connection-less.
class IpConnectionlessCommunicatorBase(IpCommunicatorBase):

    ## @brief Method to send data to a destination.
    #  @param target_ip The IP of the destination to send to.
    #  @param data The bytes to send.
    #  @return Amount of bytes sent.
    @abstractmethod
    def send_to(self, target_ip: IPvAnyAddress, data: bytes) -> int:
        raise NotImplementedError

    ## @brief Method to receive data from communicator and get the source address.
    #  @param size Amount of bytes to read.
    #  @param recv_timeout Timeout in seconds for the operation.
    #  @return The received data in bytes, and the IP of the sender.
    @abstractmethod
    def receive_from(self, size: int, recv_timeout: int) -> tuple[bytes, IPvAnyAddress]:
        raise NotImplementedError