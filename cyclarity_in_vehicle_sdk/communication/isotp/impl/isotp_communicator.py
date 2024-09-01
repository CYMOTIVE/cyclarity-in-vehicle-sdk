from typing import Optional
from cyclarity_in_vehicle_sdk.communication.base.communicator_base import CommunicatorType
from cyclarity_in_vehicle_sdk.communication.can.impl.can_communicator_socketcan import CanCommunicatorSocketCan
from cyclarity_in_vehicle_sdk.communication.isotp.base.isotp_communicator_base import Address, IsoTpCommunicatorBase
import isotp
from pydantic import Field

class IsoTpCommunicator(IsoTpCommunicatorBase):
    can_communicator: CanCommunicatorSocketCan = Field(description="CAN Communicator")
    rxid: int = Field(description="Receive CAN id.")
    txid: int = Field(description="Transmit CAN id.")

    _is_open = False
    _address = None

    def teardown(self):
        self.close()

    def model_post_init(self, *args, **kwargs):
        self._address = Address(rxid=self.rxid, txid=self.txid)

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
            self.logger.warn(f"Timeout for send operation: {str(ex)}")
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
        self.can_stack = isotp.CanStack(bus=self.can_communicator.get_bus(), address=self._address, params={"blocking_send":True})
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