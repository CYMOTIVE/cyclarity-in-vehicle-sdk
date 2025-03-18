import time
from types import TracebackType
from pydantic import Field
from cyclarity_in_vehicle_sdk.communication.can.base.can_communicator_base import CanCommunicatorBase, CanMessage, BusABC
from can.interfaces.socketcan import SocketcanBus
from typing import Optional, Sequence, Type, Union

## @class CanCommunicatorSocketCan
#  @brief This class handles the communication over the CAN bus using the SocketCAN interface.
class CanCommunicatorSocketCan(CanCommunicatorBase):
    ## @brief Name of CAN interface to work with. (e.g. can0, vcan0, etc...)
    channel: str = Field(description="Name of CAN interface to work with. (e.g. can0, vcan0, etc...)")
    ## @brief Boolean value if CAN bus supports CAN-FD.
    support_fd: bool = Field(description="CAN bus supports CAN-FD.")
    ## @brief Set of incoming CAN IDs to ignore
    blacklist_ids: set[int] = Field(default=set(), description="Incoming CAN IDs to ignore")

    ## @brief Reference to the SocketcanBus
    _bus: SocketcanBus = None

    ## @fn open
    #  @brief Open the CAN bus connection.
    def open(self) -> None:
        if self._bus:
            raise RuntimeError("CanCommunicatorSocketCan is already open")
        
        self._bus = SocketcanBus(channel=self.channel, fd=self.support_fd)

    ## @fn close
    #  @brief Close the CAN bus connection.
    def close(self) -> None:
        if self._bus:
            self._bus.shutdown()
            self._bus = None

    def __enter__(self):
        self.open()
        return self

    ## @fn __exit__
    #  @brief Close the CAN bus connection on exit.
    def __exit__(self, exception_type: Optional[type[BaseException]], exception_value: Optional[BaseException], traceback: Optional[TracebackType]) -> bool:
        self.close()
        return False

    ## @fn send
    #  @brief This function is responsible for sending a CAN message over the bus.
    #  @param can_msg This is the CAN message to be sent.
    #  @param timeout This optional parameter specifies the time to wait before the function times out. If not specified, the function will wait indefinitely.
    #  @exception RuntimeError if the CAN bus is not open.
    #  @return None
    def send(self, can_msg: CanMessage, timeout: Optional[float] = None):
        if not self._bus:
            raise RuntimeError("CanCommunicatorSocketCan has not been opened")
        
        self._bus.send(msg=can_msg, timeout=timeout)

    ## @fn send_periodically
    #  @brief This function sends CAN messages periodically over the bus.
    #  @param msgs These are the CAN messages to be sent periodically. This can be a single CAN message or a sequence of CAN messages.
    #  @param period This parameter specifies the period in seconds at which the messages are to be sent.
    #  @param duration This optional parameter specifies the total duration in seconds for which the messages are to be sent periodically. If not specified, the function will continue to send messages indefinitely.
    #  @exception RuntimeError if the CAN bus is not open.
    #  @return None
    def send_periodically(self, msgs:      Union[CanMessage, Sequence[CanMessage]],
             period:    float,
             duration:  Optional[float] = None):
        if not self._bus:
            raise RuntimeError("CanCommunicatorSocketCan has not been opened")
        
        self._bus.send_periodic(msgs=msgs, period=period, duration=duration)

    ## @fn receive
    #  @brief This function receives a CAN message from the bus.
    #  @param timeout This optional parameter specifies the maximum time in seconds to wait for a CAN message. If not specified, the function will wait indefinitely.
    #  @exception RuntimeError if the CAN bus is not open.
    #  @return The received CAN message, if any and if its arbitration ID is not in the blacklist. None otherwise.
    def receive(self, timeout: Optional[float] = None) -> Optional[CanMessage]:
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
    
    # @fn sniff
    #  @brief This function sniffs the CAN bus for a specified duration and collects all received CAN messages.
    #  @param sniff_time This parameter specifies the duration in seconds for which the function should sniff the bus.
    #  @exception RuntimeError if the CAN bus is not open.
    #  @return A list of all received CAN messages during the sniffing period. Returns None if no messages were received.
    def sniff(self, sniff_time: float) -> Optional[list[CanMessage]]:
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

    ## @fn add_to_blacklist
    #  @brief This function adds CAN IDs to the blacklist. Messages with these IDs will be ignored when received.
    #  @param canids This is a sequence of CAN IDs to be added to the blacklist.
    #  @return None
    def add_to_blacklist(self, canids: Sequence[int]):
        for canid in canids:
            self.blacklist_ids.add(canid)

    ## @fn get_bus
    #  @brief This function returns the current message bus being used for CAN communication.
    #  @exception RuntimeError if the CAN bus is not open.
    #  @return The current message bus of type BusABC.
    def get_bus(self) -> Type[BusABC]:
        if not self._bus:
            raise RuntimeError("CanCommunicatorSocketCan has not been opened")
        return self._bus