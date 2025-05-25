from typing import Literal, Optional, Union
from cyclarity_in_vehicle_sdk.protocol.uds.base.uds_utils_base import NegativeResponse, RdidDataTuple
from cyclarity_in_vehicle_sdk.protocol.uds.impl.uds_utils import UdsUtils
from cyclarity_in_vehicle_sdk.protocol.uds.models.uds_models import SESSION_INFO
from cyclarity_in_vehicle_sdk.security_testing.models import BaseTestAction, BaseTestOutput, StepResult


class ErrorCodeValidationMixin:
    def validate_error_code(self, step_output, expected_code) -> StepResult:
        if not step_output.error_code:
            return StepResult(success=False, fail_reason="Service did not return an error code")
        if expected_code:
            if expected_code == step_output.error_code:
                return StepResult(success=True)
            else:
                return StepResult(success=False, fail_reason=f"Expected {hex(expected_code)} but got {hex(step_output.error_code)}")
        else:
            return StepResult(success=False, fail_reason="Was not initalized with an error code")


# ---------------- Read DID Action and Outputs ----------------

class ReadDidOutputBase(BaseTestOutput):
    dids_data: Optional[list[RdidDataTuple]] = None
    error_code: Optional[int] = None
    
    def validate(self, step_output: "ReadDidOutputBase", prev_outputs: list["ReadDidOutputBase"] = []) -> StepResult:
        return StepResult(success=True)

class ReadDidOutputExact(ReadDidOutputBase):
    output_type: Literal['ReadDidOutputExact'] = 'ReadDidOutputExact'

    def validate(self, step_output: "ReadDidOutputBase", prev_outputs: list["ReadDidOutputBase"] = []) -> StepResult:
        if step_output.error_code:
            return StepResult(success=False, fail_reason=f"Unexpected error code {hex(step_output.error_code)}")

        if self.dids_data != step_output.dids_data:
            return StepResult(success=False, fail_reason=f"Expected {self.dids_data} but got {step_output.dids_data}")

        return StepResult(success=True)

class ReadDidOutputError(ErrorCodeValidationMixin, ReadDidOutputBase):
    output_type: Literal['ReadDidOutputError'] = 'ReadDidOutputError'
    def validate(self, step_output: "ReadDidOutputBase", prev_outputs: list["ReadDidOutputBase"] = []) -> StepResult:
        return self.validate_error_code(step_output, self.error_code)


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
    
class SessionControlOutputError(ErrorCodeValidationMixin, SessionControlOutputBase):
    output_type: Literal['SessionControlOutputError'] = 'SessionControlOutputError'
    def validate(self, step_output: SessionControlOutputBase, prev_outputs: list[SessionControlOutputBase] = []) -> StepResult:
        return self.validate_error_code(step_output, self.error_code)

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

class ECUResetOutputError(ErrorCodeValidationMixin, ECUResetOutputBase):
    output_type: Literal['ECUResetOutputError'] = 'ECUResetOutputError'
    def validate(self, step_output: ECUResetOutputBase, prev_outputs: list[ECUResetOutputBase] = []) -> StepResult:
        return self.validate_error_code(step_output, self.error_code)


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
# ---------------- Write DID Action and Outputs ----------------

class WriteDidOutputBase(BaseTestOutput):
    error_code: Optional[int] = None
    def validate(self, step_output: "WriteDidOutputBase", prev_outputs: list["WriteDidOutputBase"] = []) -> StepResult:
        return StepResult(success=True)
    
class WriteDidOutputSuccess(WriteDidOutputBase):
    output_type: Literal['WriteDidOutputSuccess'] = 'WriteDidOutputSuccess'
    def validate(self, step_output: WriteDidOutputBase, prev_outputs: list[WriteDidOutputBase] = []) -> StepResult:
        if step_output.error_code:
            return StepResult(success=False, fail_reason=f"WriteDid service failed with error code {hex(step_output.error_code)}")
        return StepResult(success=True)
    
class WriteDidOutputError(ErrorCodeValidationMixin, WriteDidOutputBase):
    output_type: Literal['WriteDidOutputError'] = 'WriteDidOutputError'
    def validate(self, step_output: WriteDidOutputBase, prev_outputs: list[WriteDidOutputBase] = []) -> StepResult:
        return self.validate_error_code(step_output, self.error_code)

class WriteDidAction(BaseTestAction):
    action_type: Literal['WriteDidAction'] = 'WriteDidAction'
    did: int
    value: str
    uds_utils: UdsUtils
    
    def execute(self) -> WriteDidOutputBase:
        try:
            self.uds_utils.setup()
            self.uds_utils.write_did(did=self.did, value=self.value)
            return WriteDidOutputBase()
        except NegativeResponse as ex:
            return WriteDidOutputBase(error_code=ex.code)
        finally:
            self.uds_utils.teardown()

# ---------------- Write DID Action and Outputs ----------------
# ---------------- Routine Control Action and Outputs ----------------

class RoutineControlOutputBase(BaseTestOutput):
    error_code: Optional[int] = None
    response_data: Optional[bytes] = None
    def validate(self, step_output: "RoutineControlOutputBase", prev_outputs: list["RoutineControlOutputBase"] = []) -> StepResult:
        return StepResult(success=True)
    
class RoutineControlOutputSuccess(RoutineControlOutputBase):
    output_type: Literal['RoutineControlOutputSuccess'] = 'RoutineControlOutputSuccess'
    def validate(self, step_output: RoutineControlOutputBase, prev_outputs: list[RoutineControlOutputBase] = []) -> StepResult:
        if step_output.error_code:
            return StepResult(success=False, fail_reason=f"RoutineControl service failed with error code {hex(step_output.error_code)}")
        
        return StepResult(success=True)
    
class RoutineControlOutputError(ErrorCodeValidationMixin, RoutineControlOutputBase):
    output_type: Literal['RoutineControlOutputError'] = 'RoutineControlOutputError'
    def validate(self, step_output: RoutineControlOutputBase, prev_outputs: list[RoutineControlOutputBase] = []) -> StepResult:
        return self.validate_error_code(step_output, self.error_code)

class RoutineControlAction(BaseTestAction):
    action_type: Literal['RoutineControlAction'] = 'RoutineControlAction'
    routine_id: int
    control_type: int
    data: Optional[bytes] = None
    uds_utils: UdsUtils
    
    def execute(self) -> RoutineControlOutputBase:
        try:
            self.uds_utils.setup()
            resp = self.uds_utils.routine_control(routine_id=self.routine_id, control_type=self.control_type, data=self.data)
            return RoutineControlOutputBase(response_data=resp.data)
        except NegativeResponse as ex:
            return RoutineControlOutputBase(error_code=ex.code)
        finally:
            self.uds_utils.teardown()

# ---------------- Routine Control Action and Outputs ----------------
