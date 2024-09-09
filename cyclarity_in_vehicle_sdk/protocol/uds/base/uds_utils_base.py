from abc import abstractmethod
from typing import Optional, TypeAlias, Union, Callable

import udsoncan
from cyclarity_sdk.expert_builder.runnable.runnable import ParsableModel
from udsoncan.services.ECUReset import ECUReset
from udsoncan.services.RoutineControl import RoutineControl
from udsoncan.services.DiagnosticSessionControl import DiagnosticSessionControl

#  type aliases
ECUResetType: TypeAlias = ECUReset.ResetType
RoutingControlResponseData: TypeAlias = RoutineControl.ResponseData
SessionControlResultData: TypeAlias = DiagnosticSessionControl.ResponseData

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
    def session(self, session: int, timeout: float, standard_version: int = udsoncan.latest_standard) -> SessionControlResultData:
        """	Diagnostic Session Control

        Args:
            timeout (float): timeout for the UDS operation in seconds
            session (int): session to switch into
            standard_version (int, optional): the version of the UDS standard we are interacting with. Defaults to udsoncan.latest_standard (2020).

        Returns:
            SessionControlResultData
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
    def read_did(self, didlist: Union[int, list[int]], timeout: float) -> dict[int, str]:
        """	Read Data By Identifier

        Args:
            timeout (float): timeout for the UDS operation in seconds
            didlist (Union[int, list[int]]): List of data identifier to read.

        Returns:
            dict[int, str]: Dictionary mapping the DID (int) with the value returned
        """
        raise NotImplementedError

    @abstractmethod
    def routing_control(self, routine_id: int, control_type: int, timeout: float, data: Optional[bytes] = None) -> RoutingControlResponseData:
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
    def write_did(self, did: int, timeout: float) -> bool:
        """Sends a request for WriteDataByIdentifier

        Args:
            timeout (float): timeout for the UDS operation in seconds
            did (int): The data identifier to write

        Returns:
            bool: True if WriteDataByIdentifier request sent successfully, False otherwise
        """
        raise NotImplementedError
    
    @abstractmethod
    def security_access(self, level: int, gen_key_cb: Callable[[bytes], bytes], timeout: float) -> bool:
        """Sends a request for SecurityAccess

        Args:
            timeout (float): timeout for the UDS operation in seconds
            level (int): The security level to unlock
            gen_key_cb (Callable[[bytes], bytes]): callback for key generation from seed, receives seed in bytes and expected to return key in bytes.

        Returns:
            bool: True if security access was allowed to the requested level. False otherwise
        """
        raise NotImplementedError