import time
from types import TracebackType
from pydantic import Field
from cyclarity_in_vehicle_sdk.communication.can.base.can_communicator_base import CanCommunicatorBase, CanMessage, BusABC
from can.interfaces.socketcan import SocketcanBus
from typing import Optional, Sequence, Type, Union

class CanCommunicatorSocketCan(CanCommunicatorBase):
    channel: str = Field(description="Name of CAN interface to work with. (e.g. can0, vcan0, etc...)")
    support_fd: bool = Field(description="CAN bus supports CAN-FD.")
    blacklist_ids: set[int] = Field(default=set(), description="Incoming CAN IDs to ignore")

    def open(self) -> None:
        if hasattr(self, "bus"):
            raise RuntimeError("CanCommunicatorSocketCan is already open")
        
        self.bus = SocketcanBus(channel=self.channel, fd=self.support_fd)

    def close(self) -> None:
        if hasattr(self, "bus"):
            self.bus.shutdown()

    def __enter__(self):
        self.open()
        return self
        
    def __exit__(self, exception_type: Optional[type[BaseException]], exception_value: Optional[BaseException], traceback: Optional[TracebackType]) -> bool:
        self.close()
        return False

    def send(self, can_msg: CanMessage, timeout: Optional[float] = None):
        if not hasattr(self, "bus"):
            raise RuntimeError("CanCommunicatorSocketCan has not been opened")
        
        self.bus.send(msg=can_msg, timeout=timeout)
    
    def send_periodically(self, msgs:      Union[CanMessage, Sequence[CanMessage]],
             period:    float,
             duration:  Optional[float] = None):
        if not hasattr(self, "bus"):
            raise RuntimeError("CanCommunicatorSocketCan has not been opened")
        
        self.bus.send_periodic(msgs=msgs, period=period, duration=duration)
    
    def receive(self, timeout: Optional[float] = None) -> Optional[CanMessage]:
        if not hasattr(self, "bus"):
            raise RuntimeError("CanCommunicatorSocketCan has not been opened")

        if not timeout:
            ret_msg = self.bus.recv()
            if ret_msg and ret_msg.arbitration_id not in self.blacklist_ids:
                return ret_msg
            else:
                return None
            
        ret_msg = None
        time_past = 0.0
        start_time = time.time()
        while time_past < timeout:
            ret_msg = self.bus.recv(timeout=timeout)
            if ret_msg and ret_msg.arbitration_id not in self.blacklist_ids:
                return ret_msg
            time_past = time.time() - start_time
        return ret_msg
        
    def sniff(self, sniff_time: float) -> Optional[list[CanMessage]]:
        if not hasattr(self, "bus"):
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
        for canid in canids:
            self.blacklist_ids.add(canid)

    def get_bus(self) -> Type[BusABC]:
        if not hasattr(self, "bus"):
            raise RuntimeError("CanCommunicatorSocketCan has not been opened")
        return self.bus