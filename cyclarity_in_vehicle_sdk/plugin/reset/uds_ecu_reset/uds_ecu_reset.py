from pydantic import Field
from cyclarity_in_vehicle_sdk.plugin.base.reset_plugin_base import ResetPluginBase
from cyclarity_in_vehicle_sdk.protocol.uds.impl.uds_utils import UdsUtils, DEFAULT_UDS_OPERATION_TIMEOUT
from cyclarity_in_vehicle_sdk.protocol.uds.base.uds_utils_base import ECUResetType

class UdsBasedEcuResetPlugin(ResetPluginBase):
    uds_utils: UdsUtils
    reset_type: int = Field(default=ECUResetType.hardReset, ge=0, le=0x7F, description="Reset type (1: hard reset, 2: key Off-On Reset, 3: Soft Reset, ..). Allowed values are from 0 to 0x7F")
    operation_timeout: float = Field(default=DEFAULT_UDS_OPERATION_TIMEOUT, gt=0, description="Timeout for the UDS operation in seconds")

    def setup(self) -> None:
        self.uds_utils.setup()

    def teardown(self) -> None:
        self.uds_utils.teardown()

    def reset(self) -> bool:
        try:
            self.logger.debug("Trying to reset the ECU")
            return self.uds_utils.ecu_reset(reset_type=self.reset_type, timeout=self.operation_timeout)
        except Exception as ex:
            self.logger.warning(f"Failed to perform UDS ECU reset. error: {ex}")
        return False