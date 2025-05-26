from typing import Any, Optional, Union, NamedTuple
from pydantic import BaseModel
from cyclarity_in_vehicle_sdk.security_testing.models import BaseTestAction, BaseTestOutput, StepResult
from cyclarity_in_vehicle_sdk.security_testing.uds_actions import (
    ReadDidAction, ReadDidOutputExact, ReadDidOutputMaskMatch, ReadDidOutputUnique, RdidDataTuple
)

TEST_ACTION_TYPES = Union[tuple(BaseTestAction.get_non_abstract_subclasses())]
TEST_OUTPUT_TYPES = Union[tuple(BaseTestOutput.get_non_abstract_subclasses())]

class TestStepTuple(BaseModel):
    action: TEST_ACTION_TYPES
    expected_output: TEST_OUTPUT_TYPES


class CyclarityTestCase(BaseModel):
    name: str
    precondition_items: list[TestStepTuple] = []
    test_items: list[TestStepTuple] = []
    postcondition_items: list[TestStepTuple] = []
    
    def setup(self) -> StepResult:
        return self._execute_and_validate(self.precondition_items)

    def run(self) -> StepResult:
        return self._execute_and_validate(self.test_items)

    def teardown(self) -> StepResult:
        return self._execute_and_validate(self.postcondition_items)

    def _execute_and_validate(self, items: list[TestStepTuple]) -> StepResult:
        result = StepResult(success=True)
        prev_outputs = []
        for i, step in enumerate(items, start=1):
            try:
                output = step.action.execute()
                result: StepResult = step.expected_output.validate(output, prev_outputs)
                if not result:
                    result.fail_reason += f"\nStep {i}/{len(items)}"
                    break
                prev_outputs.append(output)
            except Exception as ex:
                result = StepResult(success=False, fail_reason=f"Step {i}/{len(items)}, unexpected exception: {ex}")
        return result
