from abc import abstractmethod
from typing import Optional, Sequence, Type, TypeAlias, Union

import can
from cyclarity_sdk.expert_builder.runnable.runnable import ParsableModel

CanMessage: TypeAlias = can.Message
BusABC: TypeAlias = can.BusABC

## @brief Base class for CAN communicators python-can based
class CanCommunicatorBase(ParsableModel):
    
    ## @brief open the communicator
    @abstractmethod
    def open(self) -> None:
        raise NotImplementedError
    
    ## @brief close the communication
    @abstractmethod
    def close(self) -> None:
        raise NotImplementedError

    ## @brief sends CAN message over the channel
    #
    #  This is a more detailed description, which may span multiple lines.
    #  @param can_msg (CanMessage): CAN message in the python-can format `CanMessage`
    #  @param timeout (Optional[float], optional): time out in seconds. Defaults to None.
    #  @throws NotImplementedError 
    @abstractmethod
    def send(self, can_msg: CanMessage, timeout: Optional[float] = None):
        raise NotImplementedError
    
    ## @brief Send periodically CAN message(s)
    #
    #  @param msgs (Union[CanMessage, Sequence[CanMessage]]): single message or sequence of messages to be sent periodically
    #  @param period (float): time period in seconds between sending of the message(s)
    #  @param duration (Optional[float], optional): duration time in seconds to be sending the message(s) periodically. None means indefinitely.
    @abstractmethod
    def send_periodically(self, 
                          msgs:      Union[CanMessage, Sequence[CanMessage]],
                          period:    float,
                          duration:  Optional[float] = None):
        raise NotImplementedError
    
    ## @brief receive a CAN message over the channel
    #
    #  @param timeout (Optional[float], optional): timeout in seconds to try and receive. None means indefinably.
    #  @return Optional[CanMessage]: CAN message if a message was received, None otherwise.
    @abstractmethod
    def receive(self, timeout: Optional[float] = None) -> Optional[CanMessage]:
        raise NotImplementedError
    
    ## @brief sniff CAN messages from the channel for specific time
    #
    #  @param sniff_time (float): time in seconds to be sniffing the channel
    #  @return Optional[list[CanMessage]]: list of CAN messages sniffed, None if none was sniffed
    @abstractmethod
    def sniff(self, sniff_time: float) -> Optional[list[CanMessage]]:
        raise NotImplementedError
    
    ## @brief adds can IDs to a list of blacklist IDs to be ignore when sniffing or receiving
    #
    #  @param canids (Sequence[int]): CAN IDs to be added to the blacklist
    @abstractmethod
    def add_to_blacklist(self, canids: Sequence[int]):
        raise NotImplementedError

    ## @brief get the underling CAN bus 
    #
    #  @return Type[BusABC]: the CAN bus implementation - should be an implementation of BusABC
    @abstractmethod
    def get_bus(self) -> Type[BusABC]:
        raise NotImplementedError