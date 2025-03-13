from cyclarity_in_vehicle_sdk.protocol.uds.base.uds_utils_base import NegativeResponse
from cyclarity_in_vehicle_sdk.protocol.uds.models.uds_models import SESSION_INFO, UdsStandardVersion
from pydantic import Field
from cyclarity_in_vehicle_sdk.plugin.base.recover_ecu_base import RecoverEcuPluginBase
from cyclarity_in_vehicle_sdk.protocol.uds.impl.uds_utils import UdsUtils, DEFAULT_UDS_OPERATION_TIMEOUT

class UdsEcuRecoverPlugin(RecoverEcuPluginBase):
    uds_utils: UdsUtils
    session_info: SESSION_INFO = Field(description="The information of the session to recover to")
    operation_timeout: float = Field(default=DEFAULT_UDS_OPERATION_TIMEOUT, gt=0, description="Timeout for the UDS operation in seconds")
    uds_standard_version: UdsStandardVersion = Field(default=UdsStandardVersion.ISO_14229_2020.name, 
                                                     description="The standard version of the UDS in the target, defaults to latest (2020)")

    def setup(self) -> None:
        self.uds_utils.setup()

    def teardown(self) -> None:
        self.uds_utils.teardown()

    def recover(self) -> bool:
        if self.session_info.elevation_info:
            try:
                self.uds_utils.security_access(security_algorithm=self.session_info.elevation_info.security_algorithm,
                                               timeout=self.operation_timeout)     
            except NegativeResponse as nr:
                self.logger.warning(f"Got negative response trying to elevate security with the provided algorithm. attempting session switch without elevation. error: {nr.code_name}")
            except Exception as ex:
                self.logger.error(f"Failed to elevate security with the provided algorithm. attempting session switch without elevation. error: {ex}")
                
        return self.uds_utils.transit_to_session(route_to_session=self.session_info.route_to_session, 
                                                 standard_version=self.uds_standard_version, 
                                                 timeout=self.operation_timeout)
