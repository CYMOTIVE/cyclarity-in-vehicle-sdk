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
        for test_case in self.test_cases:
            if not test_case.setup():
                self.logger.error(f"Test case {test_case.name} failed in setup phase")
                self.platform_api.send_finding(TestResult(
                    topic=self.topic,
                    type=TestBasicResultType.FAILED,
                    purpose=self.purpose
                ))
                continue
            
            if not test_case.run():
                self.logger.error(f"Test case {test_case.name} failed in run phase")
                self.platform_api.send_finding(TestResult(
                    topic=self.topic,
                    type=TestBasicResultType.FAILED,
                    purpose=self.purpose
                ))
                continue

            if not test_case.teardown():
                self.logger.error(f"Test case {test_case.name} failed in teardown phase") 
                self.platform_api.send_finding(TestResult(
                    topic=self.topic,
                    type=TestBasicResultType.FAILED,
                    purpose=self.purpose
                ))
                continue
            
            self.logger.info(f"Test case {test_case.name} passed")
            self.platform_api.send_finding(TestResult(
                topic=self.topic,
                type=TestBasicResultType.PASSED,
                purpose=self.purpose
            ))

        return CyclarityTestingSuiteResult()

    def teardown(self, exception_type=None, exception_value=None, traceback=None):
        pass