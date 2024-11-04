from typing import Optional
from cyclarity_in_vehicle_sdk.communication.base.communicator_base import CommunicatorType
from cyclarity_in_vehicle_sdk.communication.can.impl.can_communicator_socketcan import CanCommunicatorSocketCan
from cyclarity_in_vehicle_sdk.communication.isotp.base.isotp_communicator_base import Address, AddressingMode, IsoTpCommunicatorBase
import isotp
from pydantic import Field

CAN_ID_MAX_NORMAL_11_BITS = 0x7FF

class IsoTpCommunicator(IsoTpCommunicatorBase):
    can_communicator: CanCommunicatorSocketCan = Field(description="CAN Communicator")
    rxid: int = Field(description="Receive CAN id.")
    txid: int = Field(description="Transmit CAN id.")
    padding_byte: Optional[int] = Field(default=None, ge=0, le=0xFF, description="Optional byte to pad TX messages with, defaults to None meaning no padding, should be in range 0x00-0xFF")
    bitrate_switch: Optional[bool] = Field(default=False, description="BRS, defaults to False")
    can_fd: Optional[bool] = Field(default=False, description="whether it is can FD, defaults to False")

    _is_open = False
    _address = None
    _params: dict = {"blocking_send":True}

    def teardown(self):
        self.close()

    def model_post_init(self, *args, **kwargs):
        super().model_post_init(self, *args, **kwargs)
        mode = AddressingMode.Normal_29bits if (self.rxid > CAN_ID_MAX_NORMAL_11_BITS or self.txid > CAN_ID_MAX_NORMAL_11_BITS) else AddressingMode.Normal_11bits
        self._address = Address(rxid=self.rxid, txid=self.txid, addressing_mode=mode)
        if self.padding_byte:
            self._params.update({"tx_padding":self.padding_byte})
        if self.bitrate_switch:
            self._params.update({"bitrate_switch":self.bitrate_switch})
        if self.can_fd:
            self._params.update({"can_fd":self.can_fd})

    def set_address(self, address: Address):
        self._address = address
        if self._is_open:
            self.can_stack.set_address(address=address)
    
    def send(self, data: bytes, timeout: Optional[float] = 1) -> int:
        if not self._is_open:
            raise RuntimeError("IsoTpCommunicator has not been opened successfully")
        
        try:
            self.can_stack.send(data=data, send_timeout=timeout)
        except isotp.BlockingSendTimeout as ex:
            self.logger.warning(f"Timeout for send operation: {str(ex)}")
            return 0
        
        return len(data)
    
    def recv(self, recv_timeout: float) -> bytes:
        if not self._is_open:
            raise RuntimeError("IsoTpCommunicator has not been opened successfully")
        
        received_data = self.can_stack.recv(block=True, timeout=recv_timeout)
        return bytes(received_data) if received_data else bytes()
    
    def open(self) -> bool:
        if not self._address:
            self.logger.error("IsoTpCommunicator has not been set with address")
            return False
        
        self.can_communicator.open()
        self.can_stack = isotp.CanStack(bus=self.can_communicator.get_bus(), address=self._address, params=self._params)
        self.can_stack.start()
        self._is_open = True
        return True
    
    def close(self) -> bool:
        if self._is_open:
            self.can_stack.stop()
            self.can_stack.reset()
            self.can_communicator.close()
            self._is_open = False

        return True
    
    def get_type(self) -> CommunicatorType:
        return CommunicatorType.ISOTP