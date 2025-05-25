from typing import Literal, Optional, Union
from cyclarity_in_vehicle_sdk.protocol.uds.base.uds_utils_base import NegativeResponse, RdidDataTuple
from cyclarity_in_vehicle_sdk.protocol.uds.impl.uds_utils import UdsUtils
from cyclarity_in_vehicle_sdk.protocol.uds.models.uds_models import SESSION_INFO
from cyclarity_in_vehicle_sdk.security_testing.models import BaseTestAction, BaseTestOutput, StepResult

# ---------------- Read DID Action and Outputs ----------------

class ReadDidOutputBase(BaseTestOutput):
    dids_data: list[RdidDataTuple] = []
    error_code: Optional[int] = None
    
    def validate(self, step_output: "ReadDidOutputBase", prev_outputs: list["ReadDidOutputBase"] = []) -> StepResult:
        return StepResult(success=True)

class ReadDidOutputExact(ReadDidOutputBase):
    output_type: Literal['ReadDidOutputExact'] = 'ReadDidOutputExact'
    def validate(self, step_output: "ReadDidOutputBase", prev_outputs: list["ReadDidOutputBase"] = []) -> StepResult:
        if self.dids_data != step_output.dids_data:
            return StepResult(success=False, fail_reason=f"Expected {self.dids_data} but got {step_output.dids_data}")
        
        if self.error_code:
            if self.error_code == step_output.error_code:
                return StepResult(success=True)
            else:
                return StepResult(success=False, fail_reason=f"Expected {hex(self.error_code)} but got {hex(step_output.error_code)}")

        return StepResult(success=True)

class ReadDidOutputMaskMatch(ReadDidOutputBase):
    output_type: Literal['ReadDidOutputMaskMatch'] = 'ReadDidOutputMaskMatch'
    mask: int
    
    def validate(self, step_output: "ReadDidOutputBase", prev_outputs: list["ReadDidOutputBase"] = []) -> StepResult:
        if step_output.error_code:
            return StepResult(success=False, fail_reason=f"Unexpected error code {hex(step_output.error_code)}")
        
        if not step_output.dids_data:
            return StepResult(success=False, fail_reason="No data returned")
        
        for actual in step_output.dids_data:
            actual_int = int(actual.data, 16)
            if actual_int & self.mask != actual_int:
                return StepResult(success=False, fail_reason=f"Data {actual.data} does not match mask {hex(self.mask)}")
        return StepResult(success=True)
    
class ReadDidOutputUnique(ReadDidOutputBase):
    output_type: Literal['ReadDidOutputUnique'] = 'ReadDidOutputUnique'
    def validate(self, step_output: "ReadDidOutputBase", prev_outputs: list["ReadDidOutputBase"] = []) -> StepResult:
        if step_output.error_code:
            return StepResult(success=False, fail_reason=f"Unexpected error code {hex(step_output.error_code)}")
        
        if not step_output.dids_data:
            return StepResult(success=False, fail_reason="No data returned")
        
        for prev_output in prev_outputs:
            for current, prev in zip(step_output.dids_data, prev_output.dids_data):
                if current.did != prev.did or current.data == prev.data:
                    return StepResult(success=False, fail_reason=f"Data {current.data} is not unique")
        return StepResult(success=True)


class ReadDidAction(BaseTestAction):
    action_type: Literal['ReadDidAction'] = 'ReadDidAction'
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
            
# ---------------- Read DID Action and Outputs ----------------
# ---------------- Session Control Action and Outputs ----------------

class SessionControlOutputBase(BaseTestOutput):
    error_code: Optional[int] = None
    def validate(self, step_output: "SessionControlOutputBase", prev_outputs: list["SessionControlOutputBase"] = []) -> StepResult:
        return StepResult(success=True)
    
class SessionControlOutputSuccess(SessionControlOutputBase):
    output_type: Literal['SessionControlOutputSuccess'] = 'SessionControlOutputSuccess'
    def validate(self, step_output: SessionControlOutputBase, prev_outputs: list[SessionControlOutputBase] = []) -> StepResult:
        if step_output.error_code:
            return StepResult(success=False, fail_reason=f"SessionControl service failed with error code {hex(self.error_code)}")
        return StepResult(success=True)
    
class SessionControlOutputError(SessionControlOutputBase):
    output_type: Literal['SessionControlOutputError'] = 'SessionControlOutputError'
    def validate(self, step_output: SessionControlOutputBase, prev_outputs: list[SessionControlOutputBase] = []) -> StepResult:
        if not step_output.error_code:
            return StepResult(success=False, fail_reason="SessionControl service did not return an error code")
        if self.error_code:
            if self.error_code == step_output.error_code:
                return StepResult(success=True)
            else:
                return StepResult(success=False, fail_reason=f"Expected {hex(self.error_code)} but got {hex(step_output.error_code)}")
        return StepResult(success=True)

class SessionControlAction(BaseTestAction):
    action_type: Literal['SessionControlAction'] = 'SessionControlAction'
    session_id: int
    uds_utils: UdsUtils
    
    def execute(self) -> SessionControlOutputBase:
        try:
            self.uds_utils.setup()
            self.uds_utils.session(session=self.session_id)
            return SessionControlOutputBase()
        except NegativeResponse as ex:
            return SessionControlOutputBase(error_code=ex.code)
        finally:
            self.uds_utils.teardown()

# ---------------- Session Control Action and Outputs ----------------
# ---------------- ECU Reset Action and Outputs ----------------

class ECUResetOutputBase(BaseTestOutput):
    error_code: Optional[int] = None
    def validate(self, step_output: "ECUResetOutputBase", prev_outputs: list["ECUResetOutputBase"] = []) -> StepResult:
        return StepResult(success=True)

class ECUResetOutputSuccess(ECUResetOutputBase):
    output_type: Literal['ECUResetOutputSuccess'] = 'ECUResetOutputSuccess'
    def validate(self, step_output: ECUResetOutputBase, prev_outputs: list[ECUResetOutputBase] = []) -> StepResult:
        if step_output.error_code:
            return StepResult(success=False, fail_reason=f"ECUReset service failed with error code {hex(step_output.error_code)}")
        return StepResult(success=True)

class ECUResetOutputError(ECUResetOutputBase):
    output_type: Literal['ECUResetOutputError'] = 'ECUResetOutputError'
    def validate(self, step_output: ECUResetOutputBase, prev_outputs: list[ECUResetOutputBase] = []) -> StepResult:
        if not step_output.error_code:
            return StepResult(success=False, fail_reason="ECUReset service did not return an error code")
        if self.error_code:
            if self.error_code == step_output.error_code:
                return StepResult(success=True)
            else:
                return StepResult(success=False, fail_reason=f"Expected {hex(self.error_code)} but got {hex(step_output.error_code)}")
        else:
            return StepResult(success=False, fail_reason="ECUResetOutputError was not initalized with an error code")


class ECUResetAction(BaseTestAction):
    action_type: Literal['ECUResetAction'] = 'ECUResetAction'
    reset_type: int
    uds_utils: UdsUtils
    
    def execute(self) -> ECUResetOutputBase:
        try:
            self.uds_utils.setup()
            self.uds_utils.ecu_reset(reset_type=self.reset_type)
            return ECUResetOutputBase()
        except NegativeResponse as ex:
            return ECUResetOutputBase(error_code=ex.code)
        finally:
            self.uds_utils.teardown()

# ---------------- ECU Reset Action and Outputs ----------------