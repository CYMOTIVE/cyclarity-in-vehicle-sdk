from cyclarity_in_vehicle_sdk.communication.base.communicator_base import CommunicatorBase
import isotp
from abc import abstractmethod
from typing import TypeAlias


# type aliases
Address: TypeAlias = isotp.Address
AddressingMode: TypeAlias = isotp.AddressingMode

class IsoTpCommunicatorBase(CommunicatorBase):
    @abstractmethod
    def set_address(self, address: Address):
        raise NotImplementedError