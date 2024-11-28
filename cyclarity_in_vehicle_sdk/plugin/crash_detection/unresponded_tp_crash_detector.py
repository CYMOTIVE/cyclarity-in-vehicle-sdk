from pydantic import Field
from cyclarity_in_vehicle_sdk.plugin.base.crash_detection_plugin_base import InteractiveCrashDetectionPluginBase
from cyclarity_in_vehicle_sdk.protocol.uds.impl.uds_utils import UdsUtils, DEFAULT_UDS_OPERATION_TIMEOUT
from cyclarity_in_vehicle_sdk.protocol.uds.base.uds_utils_base import NegativeResponse, NoResponse

class UnrespondedTesterPresentCrashDetector(InteractiveCrashDetectionPluginBase):
    uds_utils: UdsUtils
    operation_timeout: float = Field(default=DEFAULT_UDS_OPERATION_TIMEOUT, gt=0, description="Timeout for the UDS operation in seconds")

    def check_crash(self) -> bool:
        try:
            res = self.uds_utils.tester_present(timeout=self.operation_timeout)
            return res is not True
        except NoResponse:
            self.logger.debug("No response from ECU for tester present, assuming ECU has crashed")
            return True
        except NegativeResponse as nr:
            self.logger.warning(f"Got unexpected negative response from ECU. error code: {nr.code_name}")
            return False
        except Exception as ex:
            self.logger.error(f"Got unexpected exception in tester present operation. error code: {ex}")
            return False

    def setup(self) -> None:
        self.uds_utils.setup()

    def teardown(self) -> None:
        self.uds_utils.teardown()