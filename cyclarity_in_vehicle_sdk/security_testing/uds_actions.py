from typing import Literal, Optional, Union
from cyclarity_in_vehicle_sdk.protocol.uds.base.uds_utils_base import NegativeResponse, RdidDataTuple
from cyclarity_in_vehicle_sdk.protocol.uds.impl.uds_utils import UdsUtils
from cyclarity_in_vehicle_sdk.security_testing.models import BaseTestAction, BaseTestOutput, StepResult


class ReadDidOutputBase(BaseTestOutput):
    dids_data: list[RdidDataTuple] = []
    error_code: Optional[int] = None
    
    def validate(self, step_output: "ReadDidOutputBase", prev_outputs: list["ReadDidOutputBase"] = []) -> StepResult:
        return StepResult(success=True)

class ReadDidOutputExact(ReadDidOutputBase):
    action_type: Literal['ReadDidOutputExact'] = 'ReadDidOutputExact'
    def validate(self, step_output: "ReadDidOutputBase", prev_outputs: list["ReadDidOutputBase"] = []) -> StepResult:
        if self.dids_data != step_output.dids_data:
            return StepResult(success=False, fail_reason=f"Expected {self.dids_data} but got {step_output.dids_data}")
        
        if self.error_code:
            if self.error_code == step_output.error_code:
                return StepResult(success=True)
            else:
                return StepResult(success=False, fail_reason=f"Expected {self.error_code} but got {step_output.error_code}")

        return StepResult(success=True)

class ReadDidOutputMaskMatch(ReadDidOutputBase):
    action_type: Literal['ReadDidOutputMaskMatch'] = 'ReadDidOutputMaskMatch'
    mask: int
    
    def validate(self, step_output: "ReadDidOutputBase", prev_outputs: list["ReadDidOutputBase"] = []) -> StepResult:
        if self.error_code:
            return StepResult(success=False, fail_reason=f"Unexpected error code {self.error_code}")
        
        if not self.dids_data:
            return StepResult(success=False, fail_reason="No data returned")
        
        for actual in self.dids_data:
            actual_int = int(actual.data, 16)
            if actual_int & self.mask != actual_int:
                return StepResult(success=False, fail_reason=f"Data {actual.data} does not match mask {hex(self.mask)}")
        return StepResult(success=True)
    
class ReadDidOutputUnique(ReadDidOutputBase):
    action_type: Literal['ReadDidOutputUnique'] = 'ReadDidOutputUnique'
    def validate(self, step_output: "ReadDidOutputBase", prev_outputs: list["ReadDidOutputBase"] = []) -> StepResult:
        if self.error_code:
            return StepResult(success=False, fail_reason=f"Unexpected error code {self.error_code}")
        
        if not self.dids_data:
            return StepResult(success=False, fail_reason="No data returned")
        
        for prev_output in prev_outputs:
            for current, prev in zip(step_output.dids_data, prev_output.dids_data):
                if current.did != prev.did or current.data == prev.data:
                    return StepResult(success=False, fail_reason=f"Data {current.data} is not unique")
        return StepResult(success=True)


class ReadDidAction(BaseTestAction):
    dids: Union[int, list[int]]
    uds_utils: UdsUtils
    
    def execute(self) -> ReadDidOutputBase:
        try:
            self.uds_utils.setup()
            res = self.uds_utils.read_did(didlist=self.dids)
            return ReadDidOutputBase(dids_data=res)
        except NegativeResponse as ex:
            return ReadDidOutputBase(error_code=ex.code)
        finally:
            self.uds_utils.teardown()