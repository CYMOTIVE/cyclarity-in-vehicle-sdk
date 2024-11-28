from pydantic import Field
from cyclarity_in_vehicle_sdk.plugin.base.crash_detection_plugin_base import InteractiveCrashDetectionPluginBase
from cyclarity_in_vehicle_sdk.protocol.uds.impl.uds_utils import UdsUtils, DEFAULT_UDS_OPERATION_TIMEOUT
from cyclarity_in_vehicle_sdk.protocol.uds.base.uds_utils_base import NegativeResponse, NoResponse, UdsDid

class SessionChangeCrashDetector(InteractiveCrashDetectionPluginBase):
    uds_utils: UdsUtils
    current_session: int = Field(gt=1, le=0x7F, description="Session ID of current session")
    operation_timeout: float = Field(default=DEFAULT_UDS_OPERATION_TIMEOUT, gt=0, description="Timeout for the UDS operation in seconds")

    def check_crash(self) -> bool:
        try:
            res = self.uds_utils.read_did(didlist=UdsDid.ActiveDiagnosticSession, timeout=self.operation_timeout)
            active_session = int(res[UdsDid.ActiveDiagnosticSession])
            if active_session != self.current_session:
                self.logger.info(f"Active session has changed from {hex(self.current_session)} to {hex(active_session)} assuming ECU has crashed")
                return True
            
            return False
        except NoResponse:
            self.logger.warning("No response from ECU for active session read DID, assuming ECU has crashed")
            return True
        except NegativeResponse as nr:
            self.logger.error(f"Got unexpected negative response from the ECU. this plugin cannot be trusted. error code: {nr.code_name}")
            return False
        except Exception as ex:
            self.logger.error(f"Got unexpected exception in read DID operation. error code: {ex}")
            return False

    def setup(self) -> None:
        self.uds_utils.setup()

    def teardown(self) -> None:
        self.uds_utils.teardown()