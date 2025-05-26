from cyclarity_sdk.expert_builder.runnable.runnable import Runnable, BaseResultsModel
from cyclarity_sdk.sdk_models.findings.models import TestResult
from cyclarity_sdk.sdk_models.findings.types import TestBasicResultType
from cyclarity_in_vehicle_sdk.security_testing.models import StepResult
from cyclarity_in_vehicle_sdk.security_testing.test_case import CyclarityTestCase, TestStepTuple


class CyclarityTestCaseStandaloneResult(BaseResultsModel):
    pass

class CyclarityTestCaseStandalone(Runnable[CyclarityTestCaseStandaloneResult]):
    topic: str = ""
    purpose: str = ""
    name: str
    precondition_items: list[TestStepTuple] = []
    test_items: list[TestStepTuple] = []
    postcondition_items: list[TestStepTuple] = []
    
    def setup(self):
        pass

    def run(self, *args, **kwargs) -> CyclarityTestCaseStandaloneResult:
        setup_result = self._execute_and_validate(self.precondition_items)
        if not setup_result:
            self.logger.error(f"Test case \"{self.name}\" failed in setup phase, reason: {setup_result.fail_reason}")
            self.platform_api.send_finding(TestResult(
                description=f"Test Case: \"{self.name}\"",
                topic=self.topic,
                type=TestBasicResultType.FAILED,
                purpose=self.purpose,
                fail_reason=setup_result.fail_reason
            ))
            return CyclarityTestCaseStandaloneResult()

        run_result = self._execute_and_validate(self.test_items)
        if not run_result:
            self.logger.error(f"Test case \"{self.name}\" failed in run phase, reason: {run_result.fail_reason}")
            self.platform_api.send_finding(TestResult(
                description=f"Test Case: \"{self.name}\"",
                topic=self.topic,
                type=TestBasicResultType.FAILED,
                purpose=self.purpose,
                fail_reason=run_result.fail_reason
            ))
            return CyclarityTestCaseStandaloneResult()

        teardown_result = self._execute_and_validate(self.postcondition_items)
        if not teardown_result:
            self.logger.error(f"Test case \"{self.name}\" failed in teardown phase, reason: {teardown_result.fail_reason}")
            self.platform_api.send_finding(TestResult(
                description=f"Test Case: \"{self.name}\"",
                topic=self.topic,
                type=TestBasicResultType.FAILED,
                purpose=self.purpose,
                fail_reason=teardown_result.fail_reason
            ))
        return CyclarityTestCaseStandaloneResult()

    def teardown(self, exception_type=None, exception_value=None, traceback=None):
        pass

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

if __name__ == "__main__":
    from cyclarity_sdk.expert_builder import run_from_cli
    run_from_cli(CyclarityTestCaseStandalone)