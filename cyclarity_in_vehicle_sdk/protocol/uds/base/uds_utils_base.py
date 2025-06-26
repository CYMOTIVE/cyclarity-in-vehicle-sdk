from abc import abstractmethod
from typing import NamedTuple, Optional, Type, TypeAlias, Union

from cyclarity_sdk.expert_builder.runnable.runnable import ParsableModel
from udsoncan.common.dids import DataIdentifier
from udsoncan.Response import Response
from udsoncan.ResponseCode import ResponseCode
from udsoncan.services.DiagnosticSessionControl import DiagnosticSessionControl
from udsoncan.services.ECUReset import ECUReset
from udsoncan.services.ReadDTCInformation import ReadDTCInformation
from udsoncan.services.RoutineControl import RoutineControl

from cyclarity_in_vehicle_sdk.protocol.uds.models.uds_models import (
    SECURITY_ALGORITHM_BASE,
    SESSION_ACCESS,
    AuthenticationParamsBase,
    AuthenticationReturnParameter,
    UdsSid,
    UdsStandardVersion,
)

#  type aliases
ECUResetType: TypeAlias = ECUReset.ResetType
RoutingControlResponseData: TypeAlias = RoutineControl.ResponseData
SessionControlResultData: TypeAlias = DiagnosticSessionControl.ResponseData
RawUdsResponse: TypeAlias = Response
UdsResponseCode: TypeAlias = ResponseCode
UdsDefinedSessions: TypeAlias = DiagnosticSessionControl.Session
UdsDid: TypeAlias = DataIdentifier
RdidDataTuple = NamedTuple("RdidDataTuple", did=int, data=str)
DtcInformationData: TypeAlias = ReadDTCInformation.ResponseData

DEFAULT_UDS_OPERATION_TIMEOUT = 2


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
    def write_did(self, did: int, value: str | bytes, timeout: float) -> bool:
        """Sends a request for WriteDataByIdentifier

        Args:
            timeout (float): timeout for the UDS operation in seconds
            did (int): The data identifier to write
            value (str | bytes): the value to write

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
    def request_download(self, address: int, memorysize: int, enc_comp: int, address_format: int,
                         memorysize_format: int, timeout: float) -> int:
        """Send a Request Download UDS message

        Args:
            timeout (float): timeout for the UDS operation in seconds
            address (int): Block ID or address of the relevant memory region to update.
            memorysize (int): Size of the memory region to update.
            enc_comp (int, optional): Encription and Compression info.
            address_format (int, optional): Length in bytes of the Address field.
            memorysize_format (int, optional): Length in bytes of the Size field.

        :raises RuntimeError: If failed to send the request
        :raises ValueError: If parameters are out of range, missing or wrong type
        :raises NoResponse: If no response was received
        :raises InvalidResponse: with invalid reason, if invalid response has received
        :raises NegativeResponse: with error code and code name, If negative response was received

        Returns:
            int: Maximum block length for following transfer data.
        """
        raise NotImplementedError

    @abstractmethod
    def transfer_data(self, seq: int, data: bytes, timeout: float) -> None:
        """Transfer a block of data as part of Upload or Download session

        Args:
            timeout (float): timeout for the UDS operation in seconds
            seq (int): Sequence nuber of the current TransferData.
            data (bytes): Data to be transfered.

        :raises RuntimeError: If failed to send the request
        :raises ValueError: If parameters are out of range, missing or wrong type
        :raises NoResponse: If no response was received
        :raises InvalidResponse: with invalid reason, if invalid response has received
        :raises NegativeResponse: with error code and code name, If negative response was received
        """
        raise NotImplementedError

    @abstractmethod
    def transfer_exit(self, timeout: float) -> None:
        """Finish transfer session

        Args:
            data (bytes, optional): Additional optional data to send to the server
            timeout (float): timeout for the UDS operation in seconds

        :raises RuntimeError: If failed to send the request
        :raises ValueError: If parameters are out of range, missing or wrong type
        :raises NoResponse: If no response was received
        :raises InvalidResponse: with invalid reason, if invalid response has received
        :raises NegativeResponse: with error code and code name, If negative response was received

        Returns:
            bytes: The parameter records received from the transfer exit response.
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
    
    @abstractmethod
    def authentication(self,
                       params: Type[AuthenticationParamsBase],
                       timeout: float) -> AuthenticationReturnParameter:
        """Initiate UDS Authentication service sequence 

        Args:
            params (Type[AuthenticationParamsBase]): Set of parameters defined for the desired authentication task
            timeout (float): timeout for the UDS operation in seconds

        Returns:
            AuthenticationReturnParameter: The results code of the authentication action
        """
        raise NotImplementedError

    @abstractmethod
    def read_dtc_information(self, 
                           subfunction: int,
                           status_mask: Optional[int] = None,
                           severity_mask: Optional[int] = None,
                           dtc: Optional[int] = None,
                           snapshot_record_number: Optional[int] = None,
                           extended_data_record_number: Optional[int] = None,
                           memory_selection: Optional[int] = None,
                           timeout: float = DEFAULT_UDS_OPERATION_TIMEOUT,
                           standard_version: UdsStandardVersion = UdsStandardVersion.ISO_14229_2020) -> DtcInformationData:
        """Read DTC Information service (0x19)

        Args:
            subfunction (int): The service subfunction. Values are defined in ReadDTCInformation.Subfunction
            status_mask (Optional[int], optional): A DTC status mask used to filter DTC. Defaults to None.
            severity_mask (Optional[int], optional): A severity mask used to filter DTC. Defaults to None.
            dtc (Optional[int]], optional): A DTC mask used to filter DTC. Defaults to None.
            snapshot_record_number (Optional[int], optional): Snapshot record number. Defaults to None.
            extended_data_record_number (Optional[int], optional): Extended data record number. Defaults to None.
            memory_selection (Optional[int], optional): Memory selection for user defined memory DTC. Defaults to None.
            timeout (float, optional): Timeout for the UDS operation in seconds. Defaults to DEFAULT_UDS_OPERATION_TIMEOUT.
            standard_version (UdsStandardVersion, optional): the version of the UDS standard we are interacting with. Defaults to ISO_14229_2020.

        Returns:
            DtcInformationData: The DTC information response data containing the requested DTC information
        """
        raise NotImplementedError

    @abstractmethod
    def clear_diagnostic_information(self, group: int = 0xFFFFFF, memory_selection: Optional[int] = None, timeout: float = DEFAULT_UDS_OPERATION_TIMEOUT, standard_version: UdsStandardVersion = UdsStandardVersion.ISO_14229_2020) -> bool:
        """Clear Diagnostic Information service (0x14)

        Args:
            group (int, optional): DTC mask ranging from 0 to 0xFFFFFF. 0xFFFFFF means all DTCs. Defaults to 0xFFFFFF.
            memory_selection (Optional[int], optional): Number identifying the respective DTC memory. Only supported in ISO-14229-1:2020 and above. Defaults to None.
            timeout (float, optional): Timeout for the UDS operation in seconds. Defaults to DEFAULT_UDS_OPERATION_TIMEOUT.
            standard_version (UdsStandardVersion, optional): the version of the UDS standard we are interacting with. Defaults to ISO_14229_2020.

        Returns:
            bool: True if the clear operation was successful, False otherwise
        """
        raise NotImplementedError