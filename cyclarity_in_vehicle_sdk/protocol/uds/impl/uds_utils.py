from typing import Any, Callable, Optional, Union
import udsoncan.Request
import udsoncan.services
from udsoncan.Response import Response
import udsoncan.services.ECUReset
import udsoncan.services.ReadDataByIdentifier
import udsoncan.services.RoutineControl
import udsoncan.services.SecurityAccess
import udsoncan.services.TesterPresent
import udsoncan.services.WriteDataByIdentifier

from cyclarity_in_vehicle_sdk.communication.doip.doip_communicator import DoipCommunicator
from cyclarity_in_vehicle_sdk.communication.isotp.impl.isotp_communicator import IsoTpCommunicator
from cyclarity_in_vehicle_sdk.protocol.uds.base.uds_utils_base import NegativeResponse, NoResponse, RoutingControlResponseData, SessionControlResultData, UdsUtilsBase, InvalidResponse

DEFAULT_UDS_OPERATION_TIMEOUT = 2

class MyAsciiCodec(udsoncan.DidCodec):
    def __init__(self):
        pass

    def encode(self, string_ascii: Any) -> bytes:  # type: ignore
        if not isinstance(string_ascii, str):
            raise ValueError("AsciiCodec requires a string for encoding")

        return string_ascii.encode('ascii')

    def decode(self, string_bin: bytes) -> Any:
        return string_bin.hex()

    def __len__(self) -> int:
        raise udsoncan.DidCodec.ReadAllRemainingData


class UdsUtils(UdsUtilsBase):
    data_link_layer: Union[IsoTpCommunicator, DoipCommunicator]

    def setup(self) -> bool:
        """setup the library
        """
        return self.data_link_layer.open()
    
    def teardown(self):
        """Teardown the library
        """
        self.data_link_layer.close()
    
    def session(self, session: int, timeout: float = DEFAULT_UDS_OPERATION_TIMEOUT, standard_version: int = udsoncan.latest_standard) -> SessionControlResultData:
        """	Diagnostic Session Control

        Args:
            timeout (float): timeout for the UDS operation in seconds
            session (int): session to switch into
            standard_version (int, optional): the version of the UDS standard we are interacting with. Defaults to udsoncan.latest_standard (2020).
            
        :raises ValueError: If parameters are out of range, missing or wrong type
        :raises NoResponse: If no response was received
        :raises InvalidResponse: with invalid reason, if invalid response has received
        :raises NegativeResponse: with error code and code name, If negative response was received

        Returns:
            SessionControlResultData
        """
        request = udsoncan.services.DiagnosticSessionControl.make_request(session=session)
        response = self._send_and_read_response(request=request, timeout=timeout)   
        interpreted_response = udsoncan.services.DiagnosticSessionControl.interpret_response(response=response, standard_version=standard_version)
        return interpreted_response.service_data
    
    def ecu_reset(self, reset_type: int, timeout: float = DEFAULT_UDS_OPERATION_TIMEOUT) -> bool:
        """The service "ECU reset" is used to restart the control unit (ECU)

        Args:
            timeout (float): timeout for the UDS operation in seconds
            reset_type (int): type of the reset (1: hard reset, 2: key Off-On Reset, 3: Soft Reset, .. more manufacture specific types may be supported)

        :raises ValueError: If parameters are out of range, missing or wrong type
        :raises NoResponse: If no response was received
        :raises InvalidResponse: with invalid reason, if invalid response has received
        :raises NegativeResponse: with error code and code name, If negative response was received

        Returns:
            bool: True if ECU request was accepted, False otherwise.
        """
        request = udsoncan.services.ECUReset.make_request(reset_type=reset_type)
        response = self._send_and_read_response(request=request, timeout=timeout)
        interpreted_response = udsoncan.services.ECUReset.interpret_response(response=response)
        return interpreted_response.service_data.reset_type_echo == reset_type

    def read_did(self, didlist: Union[int, list[int]], timeout: float = DEFAULT_UDS_OPERATION_TIMEOUT) -> dict[int, str]:
        """	Read Data By Identifier

        Args:
            timeout (float): timeout for the UDS operation in seconds
            didlist (Union[int, list[int]]): List of data identifier to read.

        :raises ValueError: If parameters are out of range, missing or wrong type
        :raises NoResponse: If no response was received
        :raises InvalidResponse: with invalid reason, if invalid response has received
        :raises NegativeResponse: with error code and code name, If negative response was received

        Returns:
            dict[int, str]: Dictionary mapping the DID (int) with the value returned
        """
        request = udsoncan.services.ReadDataByIdentifier.make_request(didlist=didlist, didconfig=None)
        response = self._send_and_read_response(request=request, timeout=timeout)
        # attach MyAsciiCodec for every did provided
        didconfig =  {item: MyAsciiCodec() for item in ([didlist] if isinstance(didlist, int) else didlist)}
        interpreted_response = udsoncan.services.ReadDataByIdentifier.interpret_response(response=response, didlist=didlist, didconfig=didconfig)
        return self._split_dids(didlist=didlist, data_hex=list(interpreted_response.service_data.values.values())[0])

    def routing_control(self, routine_id: int, control_type: int, timeout: float = DEFAULT_UDS_OPERATION_TIMEOUT, data: Optional[bytes] = None) -> RoutingControlResponseData:
        """Sends a request for RoutineControl

        Args:
            timeout (float): timeout for the UDS operation in seconds
            routine_id (int): The routine ID
            control_type (int): Service subfunction
            data (Optional[bytes], optional): Optional additional data to provide to the server. Defaults to None.

        :raises ValueError: If parameters are out of range, missing or wrong type
        :raises NoResponse: If no response was received
        :raises InvalidResponse: with invalid reason, if invalid response has received
        :raises NegativeResponse: with error code and code name, If negative response was received

        Returns:
            RoutingControlResponseData
        """
        request = udsoncan.services.RoutineControl.make_request(routine_id=routine_id, control_type=control_type, data=data)
        response = self._send_and_read_response(request=request, timeout=timeout)
        interpreted_response = udsoncan.services.RoutineControl.interpret_response(response=response)
        return interpreted_response.service_data

    def tester_present(self, timeout: float = DEFAULT_UDS_OPERATION_TIMEOUT) -> bool:
        """Sends a request for TesterPresent

        Args:
            timeout (float): timeout for the UDS operation in seconds

        :raises ValueError: If parameters are out of range, missing or wrong type
        :raises NoResponse: If no response was received
        :raises InvalidResponse: with invalid reason, if invalid response has received
        :raises NegativeResponse: with error code and code name, If negative response was received

        Returns:
            bool: True if tester preset was accepted successfully. False otherwise
        """
        request = udsoncan.services.TesterPresent.make_request()
        response = self._send_and_read_response(request=request, timeout=timeout)
        interpreted_response = udsoncan.services.TesterPresent.interpret_response(response=response)
        return interpreted_response.service_data.subfunction_echo == 0

    def write_did(self, did: int, timeout: float = DEFAULT_UDS_OPERATION_TIMEOUT) -> bool:
        """Sends a request for WriteDataByIdentifier

        Args:
            timeout (float): timeout for the UDS operation in seconds
            did (int): The data identifier to write

        :raises ValueError: If parameters are out of range, missing or wrong type
        :raises NoResponse: If no response was received
        :raises InvalidResponse: with invalid reason, if invalid response has received
        :raises NegativeResponse: with error code and code name, If negative response was received

        Returns:
            bool: True if WriteDataByIdentifier request sent successfully, False otherwise
        """
        request = udsoncan.services.WriteDataByIdentifier.make_request(did=did, didconfig=MyAsciiCodec())
        response = self._send_and_read_response(request=request, timeout=timeout)
        interpreted_response = udsoncan.services.WriteDataByIdentifier.interpret_response(response=response)
        return interpreted_response.service_data.subfunction_echo.did_echo == did
    
    def security_access(self, level: int, gen_key_cb: Callable[[bytes], bytes], timeout: float = DEFAULT_UDS_OPERATION_TIMEOUT) -> bool:
        """Sends a request for SecurityAccess

        Args:
            timeout (float): timeout for the UDS operation in seconds
            level (int): The security level to unlock
            gen_key_cb (Callable[[bytes], bytes]): callback for key generation from seed, receives seed in bytes and expected to return key in bytes.

        :raises ValueError: If parameters are out of range, missing or wrong type
        :raises NoResponse: If no response was received
        :raises InvalidResponse: with invalid reason, if invalid response has received
        :raises NegativeResponse: with error code and code name, If negative response was received

        Returns:
            bool: True if security access was allowed to the requested level. False otherwise
        """
        request = udsoncan.services.SecurityAccess.make_request(level=level,
                                                                mode=udsoncan.services.SecurityAccess.Mode.RequestSeed)
        response = self._send_and_read_response(request=request, timeout=timeout)
        interpreted_response = udsoncan.services.SecurityAccess.interpret_response(response=response,
                                                                                   mode=udsoncan.services.SecurityAccess.Mode.RequestSeed)
        session_key = gen_key_cb(interpreted_response.service_data.seed)
        self.logger.info(session_key.hex())
        request = udsoncan.services.SecurityAccess.make_request(level=level+1,
                                                                mode=udsoncan.services.SecurityAccess.Mode.SendKey,
                                                                data=session_key)
        response = self._send_and_read_response(request=request, timeout=timeout)
        interpreted_response = udsoncan.services.SecurityAccess.interpret_response(response=response,
                                                                                   mode=udsoncan.services.SecurityAccess.Mode.SendKey)
        
        return interpreted_response.service_data.security_level_echo == level+1

    def _send_and_read_response(self, request: udsoncan.Request, timeout: float = DEFAULT_UDS_OPERATION_TIMEOUT) -> Response:
        sent_bytes = self.data_link_layer.send(data=request.get_payload(), timeout=timeout)
        if sent_bytes < len(request.get_payload()):
            self.logger.error("Failed to send request")
            raise RuntimeError("Failed to send request")
        
        raw_response = self.data_link_layer.recv(recv_timeout=timeout)

        if not raw_response:
            raise NoResponse
        
        response = Response.from_payload(payload=raw_response)
        if not response.valid:
            raise InvalidResponse(invalid_reason=response.invalid_reason)
        
        if not response.positive:
            raise NegativeResponse(code=response.code, code_name=response.code_name)
        
        return response
    
    def _split_dids(self, didlist: Union[int, list[int]], data_hex: str) -> dict[int, str]:
        if isinstance(didlist, int):
            return {didlist : data_hex}
        elif isinstance(didlist, list) and len(didlist) == 1:
            return {didlist[0] : data_hex}
        
        # handle first did
        curr_did = didlist.pop(0) 
        next_did = didlist.pop(0)
        curr_position = 0
        offset = data_hex.find(hex(next_did)[2:], curr_position)
        dids_values: dict[int, str] = {curr_did: data_hex[curr_position + 2:offset]}

        while len(didlist) > 0:
            curr_did, next_did = next_did, didlist.pop(0)
            curr_position, offset = offset, data_hex.find(hex(next_did)[2:], offset)
            dids_values.update({curr_did : data_hex[curr_position + 2:offset]})
        
        # handle last did
        dids_values.update({next_did : data_hex[offset + 2:]})

        return dids_values
