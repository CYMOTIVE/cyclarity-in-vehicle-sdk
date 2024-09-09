from abc import abstractmethod
from typing import Optional, Sequence, Type, TypeAlias, Union

import can
from cyclarity_sdk.expert_builder.runnable.runnable import ParsableModel

CanMessage: TypeAlias = can.Message
BusABC: TypeAlias = can.BusABC

class CanCommunicatorBase(ParsableModel):
    """Base class for CAN communicators python-can based
    """
    @abstractmethod
    def open(self) -> None:
        """open the communicator
        """
        raise NotImplementedError
    
    @abstractmethod
    def close(self) -> None:
        """close the communication
        """
        raise NotImplementedError

    @abstractmethod
    def send(self, can_msg: CanMessage, timeout: Optional[float] = None):
        """sends CAN message over the channel

        Args:
            can_msg (CanMessage): CAN message in the python-can format `CanMessage`
            timeout (Optional[float], optional): time out in seconds. Defaults to None.
        """
        raise NotImplementedError
    
    @abstractmethod
    def send_periodically(self, 
                          msgs:      Union[CanMessage, Sequence[CanMessage]],
                          period:    float,
                          duration:  Optional[float] = None):
        """Send periodically CAN message(s)

        Args:
            msgs (Union[CanMessage, Sequence[CanMessage]]): single message or sequence of messages to be sent periodically
            period (float): time period in seconds between sending of the message(s)
            duration (Optional[float], optional): duration time in seconds tp be sending the message(s) periodically. None means indefinitely.
        """
        raise NotImplementedError
    
    @abstractmethod
    def receive(self, timeout: Optional[float] = None) -> Optional[CanMessage]:
        """receive a CAN message over the channel

        Args:
            timeout (Optional[float], optional): timeout in seconds to try and receive. None means indefinably.

        Returns:
            Optional[CanMessage]: CAN message if a message was received, None otherwise.
        """
        raise NotImplementedError
    
    @abstractmethod
    def sniff(self, sniff_time: float) -> Optional[list[CanMessage]]:
        """sniff CAN messages from the channel for specific time

        Args:
            sniff_time (float): time in seconds to be sniffing the channel

        Returns:
            Optional[list[CanMessage]]: list of CAN messages sniffed, None if none was sniffed
        """
        raise NotImplementedError
    
    @abstractmethod
    def add_to_blacklist(self, canids: Sequence[int]):
        """adds can IDs to a list of blacklist IDs to be ignore when sniffing or receiving

        Args:
            canids (Sequence[int]): CAN IDs to be added to the blacklist
        """
        raise NotImplementedError

    @abstractmethod
    def get_bus(self) -> Type[BusABC]:
        """get the underling CAN bus 

        Returns:
            Type[BusABC]: the CAN bus implementation - should be an implementation of BusABC
        """
        raise NotImplementedError