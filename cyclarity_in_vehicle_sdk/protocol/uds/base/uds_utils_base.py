from abc import abstractmethod
from enum import IntEnum
from typing import NamedTuple, Optional, Type, TypeAlias, Union

from cyclarity_in_vehicle_sdk.protocol.uds.models.uds_models import SECURITY_ALGORITHM_BASE, SESSION_ACCESS, UdsStandardVersion
from udsoncan.Response import Response
from udsoncan.ResponseCode import ResponseCode
from cyclarity_sdk.expert_builder.runnable.runnable import ParsableModel
from udsoncan.services.ECUReset import ECUReset
from udsoncan.services.RoutineControl import RoutineControl
from udsoncan.services.DiagnosticSessionControl import DiagnosticSessionControl
from udsoncan.common.dids import DataIdentifier

#  type aliases
ECUResetType: TypeAlias = ECUReset.ResetType
RoutingControlResponseData: TypeAlias = RoutineControl.ResponseData
SessionControlResultData: TypeAlias = DiagnosticSessionControl.ResponseData
RawUdsResponse: TypeAlias = Response
UdsResponseCode: TypeAlias = ResponseCode
UdsDefinedSessions: TypeAlias = DiagnosticSessionControl.Session
UdsDid: TypeAlias = DataIdentifier
RdidDataTuple = NamedTuple("RdidDataTuple", did=int, data=str)

class UdsSid(IntEnum):
    """The service IDs standardized by UDS.

    For additional information, see https://en.wikipedia.org/wiki/Unified_Diagnostic_Services
    """

    # 0x10..0x3e: UDS standardized service IDs
    DiagnosticSessionControl = 0x10
    EcuReset = 0x11
    SecurityAccess = 0x27
    CommunicationControl = 0x28
    Authentication = 0x29
    TesterPresent = 0x3E
    AccessTimingParameters = 0x83
    SecuredDataTransmission = 0x84
    ControlDtcSettings = 0x85
    ResponseOnEvent = 0x86
    LinkControl = 0x87
    ReadDataByIdentifier = 0x22
    ReadMemoryByAddress = 0x23
    ReadScalingDataByIdentifier = 0x24
    ReadDataByIdentifierPeriodic = 0x2A
    DynamicallyDefineDataIdentifier = 0x2C
    WriteDataByIdentifier = 0x2E
    WriteMemoryByAddress = 0x3D
    ClearDiagnosticInformation = 0x14
    ReadDtcInformation = 0x19
    InputOutputControlByIdentifier = 0x2F
    RoutineControl = 0x31
    RequestDownload = 0x34
    RequestUpload = 0x35
    TransferData = 0x36
    RequestTransferExit = 0x37
    RequestFileTransfer = 0x38

class NoResponse(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__("No response received for UDS request")

class NegativeResponse(Exception):
    code: int
    code_name: str
    def __init__(self, code: int, code_name: str, *args, **kwargs):
        self.code = code
        self.code_name = code_name
        super().__init__(f"Negative Response received, code: {hex(code)}, code name: {code_name}", *args, **kwargs)

class InvalidResponse(Exception):
    invalid_reason: str
    def __init__(self, invalid_reason: str, *args, **kwargs):
        self.invalid_reason = invalid_reason
        super().__init__(f"Invalid Response received, invalid reason: {invalid_reason}", *args, **kwargs)

class UdsUtilsBase(ParsableModel):
    """UDS Utility Base class API allowing common UDS functionality - this API is based on types from `udsoncan`
    """

    @abstractmethod
    def setup(self) -> bool:
        """setup the library
        """
        raise NotImplementedError
    
    @abstractmethod
    def teardown(self):
        """Teardown the library
        """
        raise NotImplementedError

    @abstractmethod
    def session(self, session: int, timeout: float, standard_version: UdsStandardVersion = UdsStandardVersion.ISO_14229_2020) -> SessionControlResultData:
        """	Diagnostic Session Control

        Args:
            timeout (float): timeout for the UDS operation in seconds
            session (int): session to switch into
            standard_version (UdsStandardVersion, optional): the version of the UDS standard we are interacting with. Defaults to ISO_14229_2020.

        Returns:
            SessionControlResultData
        """
        raise NotImplementedError
    
    def transit_to_session(self, route_to_session: list[SESSION_ACCESS], timeout: float, standard_version: UdsStandardVersion = UdsStandardVersion.ISO_14229_2020) -> bool:
        """Transit to the UDS session according to route

        Args:
            route_to_session (list[SESSION_ACCESS]): list of UDS SESSION_ACCESS objects to follow
            timeout (float): timeout for the UDS operation in seconds
            standard_version (UdsStandardVersion, optional): the version of the UDS standard we are interacting with. Defaults to ISO_14229_2020.

        Returns:
            bool: True if succeeded to transit to the session, False otherwise 
        """
        raise NotImplementedError
    
    @abstractmethod
    def ecu_reset(self, reset_type: int, timeout: float) -> bool:
        """The service "ECU reset" is used to restart the control unit (ECU)

        Args:
            timeout (float): timeout for the UDS operation in seconds
            reset_type (int): type of the reset (1: hard reset, 2: key Off-On Reset, 3: Soft Reset, .. more manufacture specific types may be supported)

        Returns:
            bool: True if ECU request was accepted, False otherwise.
        """
        raise NotImplementedError

    @abstractmethod
    def read_did(self, didlist: Union[int, list[int]], timeout: float) -> list[RdidDataTuple]:
        """	Read Data By Identifier

        Args:
            timeout (float): timeout for the UDS operation in seconds
            didlist (Union[int, list[int]]): List of data identifier to read.

        Returns:
            dict[int, str]: Dictionary mapping the DID (int) with the value returned
        """
        raise NotImplementedError

    @abstractmethod
    def routine_control(self, routine_id: int, control_type: int, timeout: float, data: Optional[bytes] = None) -> RoutingControlResponseData:
        """Sends a request for RoutineControl

        Args:
            timeout (float): timeout for the UDS operation in seconds
            routine_id (int): The routine ID
            control_type (int): Service subfunction
            data (Optional[bytes], optional): Optional additional data to provide to the server. Defaults to None.

        Returns:
            RoutingControlResponseData
        """
        raise NotImplementedError

    @abstractmethod
    def tester_present(self, timeout: float) -> bool:
        """Sends a request for TesterPresent

        Args:
            timeout (float): timeout for the UDS operation in seconds

        Returns:
            bool: True if tester preset was accepted successfully. False otherwise
        """
        raise NotImplementedError

    @abstractmethod
    def write_did(self, did: int, value: str, timeout: float) -> bool:
        """Sends a request for WriteDataByIdentifier

        Args:
            timeout (float): timeout for the UDS operation in seconds
            did (int): The data identifier to write
            value (str): the value to write

        Returns:
            bool: True if WriteDataByIdentifier request sent successfully, False otherwise
        """
        raise NotImplementedError
    
    @abstractmethod
    def security_access(self, security_algorithm: Type[SECURITY_ALGORITHM_BASE], timeout: float) -> bool:
        """Sends a request for SecurityAccess

        Args:
            timeout (float): timeout for the UDS operation in seconds
            security_algorithm (Type[SECURITY_ALGORITHM_BASE]): security algorithm to use for security access

        Returns:
            bool: True if security access was allowed to the requested level. False otherwise
        """
        raise NotImplementedError
    
    @abstractmethod
    def raw_uds_service(self, sid: UdsSid, timeout: float, sub_function: Optional[int] = None, data: Optional[bytes] = None) -> RawUdsResponse:
        """sends raw UDS service request and reads response

        Args:
            sid (UdsSid): Service ID of the request
            timeout (float): timeout for the UDS operation in seconds
            sub_function (Optional[int], optional): The service subfunction. Defaults to None.
            data (Optional[bytes], optional): The service data. Defaults to None.

        Returns:
            RawUdsResponse: Raw UdsResponse
        """
        raise NotImplementedError