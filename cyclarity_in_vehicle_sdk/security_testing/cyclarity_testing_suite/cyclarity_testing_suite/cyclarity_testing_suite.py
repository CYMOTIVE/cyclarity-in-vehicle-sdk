from cyclarity_sdk.expert_builder.runnable.runnable import Runnable, BaseResultsModel
from cyclarity_sdk.sdk_models.findings.models import TestResult
from cyclarity_sdk.sdk_models.findings.types import TestBasicResultType
from cyclarity_in_vehicle_sdk.security_testing.test_case import CyclarityTestCase


class CyclarityTestingSuiteResult(BaseResultsModel):
    pass


class CyclarityTestingSuite(Runnable[CyclarityTestingSuiteResult]):
    topic: str
    purpose: str
    test_cases: list[CyclarityTestCase] = []
    
    def setup(self) -> None:
        pass

    def run(self, *args, **kwargs) -> CyclarityTestingSuiteResult:
        """Execute all test cases in the suite.
        """
        self.logger.info(f"Executing {len(self.test_cases)} test cases")
        try:
            for test_case in self.test_cases:
                setup_result = test_case.setup()
                if not setup_result:
                    self.logger.error(f"Test case \"{test_case.name}\" failed in setup phase, reason: {setup_result.fail_reason}")
                    self.platform_api.send_finding(TestResult(
                        topic=self.topic,
                        type=TestBasicResultType.FAILED,
                        purpose=self.purpose,
                        fail_reason=setup_result.fail_reason
                    ))
                    continue
                
                run_result = test_case.run()
                if not run_result:
                    self.logger.error(f"Test case \"{test_case.name}\" failed in run phase, reason: {run_result.fail_reason}")
                    self.platform_api.send_finding(TestResult(
                        topic=self.topic,
                        type=TestBasicResultType.FAILED,
                        purpose=self.purpose,
                        fail_reason=run_result.fail_reason
                    ))
                    continue

                teardown_result = test_case.teardown()
                if not teardown_result:
                    self.logger.error(f"Test case \"{test_case.name}\" failed in teardown phase, reason: {teardown_result.fail_reason}") 
                    self.platform_api.send_finding(TestResult(
                        topic=self.topic,
                        type=TestBasicResultType.FAILED,
                        purpose=self.purpose,
                        fail_reason=teardown_result.fail_reason
                    ))
                    continue
                
                self.logger.info(f"Test case \"{test_case.name}\" passed")
                self.platform_api.send_finding(TestResult(
                    topic=self.topic,
                    type=TestBasicResultType.PASSED,
                    purpose=self.purpose
                ))
        except Exception as e:
            self.logger.error(f"Test case \"{test_case.name}\" failed with exception: {e}")
            self.platform_api.send_finding(TestResult(
                topic=self.topic,
                type=TestBasicResultType.FAILED,
                purpose=self.purpose,
                fail_reason=str(e)
            ))

        return CyclarityTestingSuiteResult()

    def teardown(self, exception_type=None, exception_value=None, traceback=None):
        pass
    
if __name__ == "__main__":
    from cyclarity_sdk.expert_builder import run_from_cli
    run_from_cli(CyclarityTestingSuite)