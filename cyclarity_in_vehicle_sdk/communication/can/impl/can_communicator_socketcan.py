import time
from types import TracebackType
from pydantic import Field
from cyclarity_in_vehicle_sdk.communication.can.base.can_communicator_base import CanCommunicatorBase, CanMessage, BusABC
from can.interfaces.socketcan import SocketcanBus
from typing import Optional, Sequence, Type, Union

class CanCommunicatorSocketCan(CanCommunicatorBase):
    """This class handles the communication over the CAN bus using the SocketCAN interface."
    """
    channel: str = Field(description="Name of CAN interface to work with. (e.g. can0, vcan0, etc...)")
    support_fd: bool = Field(description="CAN bus supports CAN-FD.")
    blacklist_ids: set[int] = Field(default=set(), description="Incoming CAN IDs to ignore")

    _bus: SocketcanBus = None

    def open(self) -> None:
        """Opens the communicator. this method must be called before usage.
        """
        if self._bus:
            raise RuntimeError("CanCommunicatorSocketCan is already open")
        
        self._bus = SocketcanBus(channel=self.channel, fd=self.support_fd)

    def close(self) -> None:
        """Closes the communicator.
        """
        if self._bus:
            self._bus.shutdown()
            self._bus = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exception_type: Optional[type[BaseException]], exception_value: Optional[BaseException], traceback: Optional[TracebackType]) -> bool:
        self.close()
        return False

    def send(self, can_msg: CanMessage, timeout: Optional[float] = None):
        """Transmit a message to the CAN bus.

        Args:
            can_msg (CanMessage): CAN message in the python-can format `CanMessage`
            timeout (Optional[float], optional): time out in seconds. Defaults to None.
        """
        if not self._bus:
            raise RuntimeError("CanCommunicatorSocketCan has not been opened")
        
        self._bus.send(msg=can_msg, timeout=timeout)

    def send_periodically(self,
                          msgs: Union[CanMessage, Sequence[CanMessage]],
                          period:    float,
                          duration:  Optional[float] = None):
        """Send periodically CAN message(s)

        Args:
            msgs (Union[CanMessage, Sequence[CanMessage]]): single message or sequence of messages to be sent periodically
            period (float): time period in seconds between sending of the message(s)
            duration (Optional[float], optional): duration time in seconds tp be sending the message(s) periodically. None means indefinitely.
        """
        if not self._bus:
            raise RuntimeError("CanCommunicatorSocketCan has not been opened")
        
        self._bus.send_periodic(msgs=msgs, period=period, duration=duration)

    def receive(self, timeout: Optional[float] = None) -> Optional[CanMessage]:
        """receive a CAN message over the channel

        Args:
            timeout (Optional[float], optional): timeout in seconds to try and receive. None means indefinably.

        Returns:
            Optional[CanMessage]: CAN message if a message was received, None otherwise.
        """
        if not self._bus:
            raise RuntimeError("CanCommunicatorSocketCan has not been opened")
        
        if not timeout:
            ret_msg = self._bus.recv()
            if ret_msg and ret_msg.arbitration_id not in self.blacklist_ids:
                return ret_msg
            else:
                return None
            
        time_past = 0.0
        start_time = time.time()
        while time_past < timeout:
            ret_msg = self._bus.recv(timeout=timeout)
            if ret_msg and ret_msg.arbitration_id not in self.blacklist_ids:
                return ret_msg
            time_past = time.time() - start_time
        return None

    def sniff(self, sniff_time: float) -> Optional[list[CanMessage]]:
        """sniff CAN messages from the channel for specific time

        Args:
            sniff_time (float): time in seconds to be sniffing the channel

        Returns:
            Optional[list[CanMessage]]: list of CAN messages sniffed, None if none was sniffed
        """
        if not self._bus:
            raise RuntimeError("CanCommunicatorSocketCan has not been opened")
        
        ret_msgs: list[CanMessage] = []
        start_time = time.time()
        time_passed = 0
        while time_passed < sniff_time:
            m = self.receive(timeout=(sniff_time - time_passed))
            if m:
                ret_msgs.append(m)
            time_passed = time.time() - start_time
        return ret_msgs

    def add_to_blacklist(self, canids: Sequence[int]):
        """adds can IDs to a list of blacklist IDs to be ignore when sniffing or receiving

        Args:
            canids (Sequence[int]): CAN IDs to be added to the blacklist
        """
        for canid in canids:
            self.blacklist_ids.add(canid)

    def get_bus(self) -> Type[BusABC]:
        """get the underling CAN bus 

        Returns:
            Type[BusABC]: the CAN bus implementation - should be an implementation of BusABC
        """
        if not self._bus:
            raise RuntimeError("CanCommunicatorSocketCan has not been opened")
        return self._bus