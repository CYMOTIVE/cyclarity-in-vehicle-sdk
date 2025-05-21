from typing import Union
from cyclarity_in_vehicle_sdk.protocol.uds.base.uds_utils_base import NegativeResponse, RdidDataTuple
from cyclarity_in_vehicle_sdk.protocol.uds.impl.uds_utils import UdsUtils
from cyclarity_in_vehicle_sdk.security_testing.models import BaseTestAction, BaseTestOutput


class ReadDidOutputBase(BaseTestOutput):
    dids_data: list[RdidDataTuple] = []
    error_code: int = None
    
    def is_success(self, step_output: "ReadDidOutputBase", prev_outputs: list["ReadDidOutputBase"] = []) -> bool:
        return True

class ReadDidOutputExact(ReadDidOutputBase):
    def is_success(self, step_output: "ReadDidOutputBase", prev_outputs: list["ReadDidOutputBase"] = []) -> bool:
        if self.dids_data != step_output.dids_data:
            return False
        
        if self.error_code:
            return self.error_code == step_output.error_code

        return True

class ReadDidOutputMaskMatch(ReadDidOutputBase):
    mask: int
    
    def is_success(self, step_output: "ReadDidOutputBase", prev_outputs: list["ReadDidOutputBase"] = []) -> bool:
        if self.error_code:
            return False
        
        if not self.dids_data:
            return False
        
        for actual in self.dids_data:
            actual_int = int(actual.data, 16)
            return actual_int & self.mask == actual_int
        return True
    
class ReadDidOutputUnique(ReadDidOutputBase):
    def is_success(self, step_output: "ReadDidOutputBase", prev_outputs: list["ReadDidOutputBase"] = []) -> bool:
        if self.error_code:
            return False
        
        if not self.dids_data:
            return False
        
        for prev_output in prev_outputs:
            for current, prev in zip(step_output.dids_data, prev_output.dids_data):
                if current.did != prev.did or current.data == prev.data:
                    return False
            
        return True


class ReadDidAction(BaseTestAction):
    dids: Union[int, list[int]]
    uds_utils: UdsUtils
    
    def execute(self) -> ReadDidOutputBase:
        try:
            res = self.uds_utils.read_did(didlist=self.dids)
            return ReadDidOutputBase(dids_data=res)
        except NegativeResponse as ex:
            return ReadDidOutputBase(error_code=ex.code)