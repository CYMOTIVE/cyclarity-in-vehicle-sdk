import asyncio
from pydantic import Field
from cyclarity_in_vehicle_sdk.plugin.base.crash_detection_plugin_base import CrashDetectionPluginBase
from cyclarity_in_vehicle_sdk.protocol.uds.impl.uds_utils import UdsUtils, DEFAULT_UDS_OPERATION_TIMEOUT
from cyclarity_in_vehicle_sdk.protocol.uds.base.uds_utils_base import NegativeResponse, NoResponse, UdsDid

class SessionChangeCrashDetector(CrashDetectionPluginBase):
    uds_utils: UdsUtils
    current_session: int = Field(gt=1, le=0x7F, description="Session ID of current session")
    inquiry_interval: float = Field(default=1, gt=0, description="The interval in seconds between active session inquiry")
    operation_timeout: float = Field(default=DEFAULT_UDS_OPERATION_TIMEOUT, gt=0, description="Timeout for the UDS operation in seconds")

    async def run(self) -> None:
        if not self._sanity_check():
            self._error_notifier_cb()
            return
        
        while True:
            try:
                res = self.uds_utils.read_did(didlist=UdsDid.ActiveDiagnosticSession)
                active_session = int(res[UdsDid.ActiveDiagnosticSession])
                if active_session != self.current_session:
                    self.logger.debug(f"Active session has changed from {hex(self.current_session)} to {hex(active_session)} assuming ECU has crashed")
                    self._event_notifier_cb()
            except NoResponse:
                self.logger.debug("No response from ECU for active session read DID, assuming ECU has crashed")
                self._event_notifier_cb()
            except NegativeResponse as nr:
                self.logger.debug(f"Got unexpected negative response from ECU, assuming ECU has crashed. error code: {nr.code_name}")
                self._event_notifier_cb()
            except Exception as ex:
                self.logger.debug(f"Got unexpected exception in read DID operation, assuming ECU has crashed. error code: {ex}")
                self._event_notifier_cb()
            finally:
                await asyncio.sleep(delay=self.inquiry_interval)

    
    def _sanity_check(self) -> bool:
        try:
            res = self.uds_utils.read_did(didlist=UdsDid.ActiveDiagnosticSession)
            active_session = int(res[UdsDid.ActiveDiagnosticSession])
            if active_session != self.current_session:
                self.logger.error(f"Active session is not has expected got {hex(active_session)}, expected {hex(self.current_session)}, sanity check failed")
                return False
            
            self.logger.debug("Sanity check succeeded")
            return True
        except Exception as ex:
            self.logger.error(f"Got unexpected exception: {ex}, sanity check failed")
            return False

    def setup(self) -> None:
        self.uds_utils.setup()

    def teardown(self) -> None:
        self.uds_utils.teardown()