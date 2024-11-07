from cyclarity_in_vehicle_sdk.protocol.uds.models.uds_models import SESSION_INFO
from pydantic import Field
from cyclarity_in_vehicle_sdk.plugin.base.recover_ecu_base import RecoverEcuPluginBase
from cyclarity_in_vehicle_sdk.protocol.uds.impl.uds_utils import UdsUtils, DEFAULT_UDS_OPERATION_TIMEOUT
from cyclarity_in_vehicle_sdk.protocol.uds.base.uds_utils_base import ECUResetType

class UdsEcuRecoverPlugin(RecoverEcuPluginBase):
    uds_utils: UdsUtils
    session_info: SESSION_INFO = Field(description="The information of the session to recover to")
    operation_timeout: float = Field(default=DEFAULT_UDS_OPERATION_TIMEOUT, gt=0, description="Timeout for the UDS operation in seconds")
    uds_standard_version: int = Field(default=2020, description="The standard version of the UDS in the target, defaults to latest (2020)")

    def setup(self) -> None:
        self.uds_utils.setup()

    def teardown(self) -> None:
        self.uds_utils.teardown()

    def recover(self) -> bool:
        return self.uds_utils.transit_to_session(route_to_session=self.session_info.route_to_session, 
                                                 standard_version=self.uds_standard_version, 
                                                 timeout=self.operation_timeout)
