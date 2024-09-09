
from abc import abstractmethod
from typing import Callable, Optional
from cyclarity_sdk.expert_builder.runnable.runnable import ParsableModel
from py_pcapplusplus import Packet

class RawSocketCommunicatorBase(ParsableModel):
    """base class for raw socket packet communicators
    """
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
    def send(self, packet: Packet) -> bool:
        """send a packet of the raw socket

        Args:
            packet (Packet): packet o send

        Returns:
            bool: True if sent successfully, False otherwise
        """
        raise NotImplementedError

    @abstractmethod
    def send_receive_packet(self, packet: Packet, is_answer: Callable[[Packet], bool], timeout: float) -> Optional[Packet]:
        """send packet and read an answer

        Args:
            packet (Packet): packet to send_
            is_answer (Callable[[Packet], bool]): callback that receives a packet and returns true if this packet is the answer to sent one
            timeout (int): timeout for the operation

        Returns:
            Packet: the answer to the packet, None if not found
        """
        raise NotImplementedError
    
    @abstractmethod
    def receive(self, timeout: float) -> Optional[Packet]:
        """read a single packet from the socket

        Args:
            timeout (int): timeout for the operation

        Returns:
            Packet: the read packet
        """
        raise NotImplementedError
