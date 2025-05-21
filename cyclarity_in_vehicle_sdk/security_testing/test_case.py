from typing import Union, NamedTuple
from pydantic import BaseModel
from cyclarity_in_vehicle_sdk.security_testing.models import BaseTestAction, BaseTestOutput
from cyclarity_in_vehicle_sdk.security_testing.uds_actions import (
    ReadDidAction, ReadDidOutputExact, ReadDidOutputMaskMatch, ReadDidOutputUnique, RdidDataTuple
)

TEST_ACTION_TYPES = Union[tuple(BaseTestAction.get_non_abstract_subclasses())]
TEST_OUTPUT_TYPES = Union[tuple(BaseTestOutput.get_non_abstract_subclasses())]

class TestStepTuple(NamedTuple):
    action: TEST_ACTION_TYPES
    expected_output: TEST_OUTPUT_TYPES


class CyclarityTestCase(BaseModel):
    name: str
    precondition_items: list[TestStepTuple] = []
    test_items: list[TestStepTuple] = []
    postcondition_items: list[TestStepTuple] = []
    
    def setup(self) -> bool:
        return self._execute_and_validate(self.precondition_items)

    def run(self) -> bool:
        return self._execute_and_validate(self.test_items)

    def teardown(self) -> bool:
        return self._execute_and_validate(self.postcondition_items)

    def _execute_and_validate(self, items: list[TestStepTuple]) -> bool:
        success = True
        prev_outputs = []
        for step in items:
            output = step.action.execute()
            if not step.expected_output.is_success(output, prev_outputs):
                success = False
                break
            prev_outputs.append(output)
        return success
