
from abc import abstractmethod
from typing import Callable, Sequence
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
    def is_open(self) -> bool:
        """inform the state of the raw socket

        Returns:
            bool: True if the socket is open and ready for send/receive operations, False otherwise.
        """
        raise NotImplementedError
    
    @abstractmethod
    def send_packet(self, packet: Packet) -> bool:
        """send a packet or a sequence of packets to the raw socket

        Args:
            packet (Packet | Sequence[Packet]): packet/packets to send.

        Returns:
            bool: True if sent successfully, False otherwise
        """
        raise NotImplementedError
    
    def send_packets(self, packets: Sequence[Packet]) -> bool:
        """send a sequence of packets to the raw socket
        
        Note: This function uses the implementation of 'send_packet', 
        Optionally override this function to have a better implementation.

        Args:
            packet (Packet | Sequence[Packet]): packet/packets to send.

        Returns:
            bool: True if sent successfully, False otherwise
        """
        for i, packet in enumerate(packets):
            if not self.send_packet(packet):
                self.logger.error(f"Could not send packet {i} of of {len(packets)}")
                return False
        return True
        
    def send(self, packet: Packet | Sequence[Packet]) -> bool:
        """send a packet or a sequence of packets to the raw socket

        Args:
            packet (Packet | Sequence[Packet]): packet/packets to send.

        Returns:
            bool: True if sent successfully, False otherwise
        """
        if self.is_open():
            if isinstance(packet, Sequence):
                return self.send_packets(packet)
            else:
                return self.send_packet(packet)
        else:
            self.logger.error("Attempting to send packets without openning the socket.")
            return False

    def send_receive_packet(self, packet: Packet | Sequence[Packet] | None, is_answer: Callable[[Packet], bool], timeout: float) -> Packet | None:
        """send packet or a sequence of packets and read an answer
        The answer is one packet that satisfy the "is_answer" callback provided.

        Note: This function uses the implementation of 'send_receive_packets', 
        Optionally override this function to have a better implementation (stop after the first valid packet arrives).

        Args:
            packet (Packet | Sequence[Packet] | None): the packet/packets to send. None to skip the sending operation.
            is_answer (Callable[[Packet], bool]): callback that receives a packet and returns True if this packet is the answer to sent one
            timeout (int): timeout for the operation

        Returns:
            Packet | None: The first packet that satisfy the "is_answer" callback, None if not found.
        """
        found_packets = self.send_receive_packets(packet, is_answer, timeout)
        if found_packets:
            return found_packets[0] # Get first valid answer
        else:
            return None
    
    @abstractmethod
    def send_receive_packets(self, packet: Packet | Sequence[Packet] | None, is_answer: Callable[[Packet], bool], timeout: float) -> list[Packet]:
        """send packet or a sequence of packets and read a multiple packets answer
        The answer is a list of packets that satisfy the "is_answer" callback provided.

        Args:
            packet (Packet | Sequence[Packet] | None): the packet/packets to send. None to skip the sending operation.
            is_answer (Callable[[Packet], bool]): callback that receives a packet and returns True if this packet is the answer to sent one
            timeout (int): timeout for the operation

        Returns:
            list[Packet]: All packets received that satisfy the "is_answer" callback.
        """ 
        raise NotImplementedError

    @abstractmethod
    def receive(self, timeout: float) -> Packet | None:
        """read a single packet from the socket

        Args:
            timeout (float): timeout in seconds for the operation, 0 for blocking receive.

        Returns:
            Packet | None: the read packet, None if timeout reached.
        """
        raise NotImplementedError

    def receive_answer(self, is_answer: Callable[[Packet], bool], timeout: float) -> Packet | None:
        """sniff communication and return a packet that satisfy the "is_answer" callback.

        Args:
            (Callable[[Packet], bool]): A callback that receives a packet and returns True if this packet is the answer looking for.
            timeout (float): The duration of the sniffing to locate the answer packet.

        Returns:
            Packet | None: The first packet that satisfy the "is_answer" callback, None if not found.
        """
        return self.send_receive_packet(None, is_answer, timeout)
    
    def receive_answers(self, is_answer: Callable[[Packet], bool], timeout: float) -> Packet | None:
        """Read a multiple packets and returns all packets that satisfy the "is_answer" callback provided.

        Args:
            is_answer (Callable[[Packet], bool]): A callback that receives a packet and returns True if this packet is the answer looking for.
            timeout (int): The duration of the sniffing to locate the answer packets.

        Returns:
            list[Packet]: All packets received that satisfy the "is_answer" callback.
        """ 
        return self.send_receive_packets(None, is_answer, timeout)

    def __del__(self):
        if self.is_open():
            self.logger.error(f"Destructor of raw socket {self.__class__.__name__} called without closing it first. Forcly closing the socket.")
            self.close()

