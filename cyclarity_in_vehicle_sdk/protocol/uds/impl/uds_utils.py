import time
from typing import Optional, Type, Union

from pydantic import Field
from udsoncan import MemoryLocation, DataFormatIdentifier
from udsoncan.BaseService import BaseService
from udsoncan.common.DidCodec import DidCodec
from udsoncan.Request import Request
from udsoncan.services import (
    Authentication,
    ClearDiagnosticInformation,
    DiagnosticSessionControl,
    ECUReset,
    ReadDataByIdentifier,
    ReadDTCInformation,
    RoutineControl,
    RequestDownload,
    TransferData,
    RequestTransferExit,
    SecurityAccess,
    TesterPresent,
    WriteDataByIdentifier,
)

from cyclarity_in_vehicle_sdk.communication.doip.doip_communicator import (
    DoipCommunicator,
)
from cyclarity_in_vehicle_sdk.communication.isotp.impl.isotp_communicator import (
    IsoTpCommunicator,
)
from cyclarity_in_vehicle_sdk.protocol.uds.base.uds_utils_base import (
    DEFAULT_UDS_OPERATION_TIMEOUT,
    AuthenticationReturnParameter,
    DtcInformationData,
    InvalidResponse,
    NegativeResponse,
    NoResponse,
    RawUdsResponse,
    RdidDataTuple,
    RoutingControlResponseData,
    SessionControlResultData,
    UdsResponseCode,
    UdsSid,
    UdsUtilsBase,
)
from cyclarity_in_vehicle_sdk.protocol.uds.models.uds_models import (
    SECURITY_ALGORITHM_BASE,
    SESSION_ACCESS,
    AuthenticationAction,
    AuthenticationParamsBase,
    TransmitCertificateParams,
    UdsStandardVersion,
    UnidirectionalAPCEParams,
)
from cyclarity_in_vehicle_sdk.utils.crypto.crypto_utils import CryptoUtils

RAW_SERVICES_WITH_SUB_FUNC = {value: type(name, (BaseService,), {'_sid':value, '_use_subfunction':True}) for name, value in UdsSid.__members__.items()}  
RAW_SERVICES_WITHOUT_SUB_FUNC = {value: type(name, (BaseService,), {'_sid':value, '_use_subfunction':False}) for name, value in UdsSid.__members__.items()}  

class HexStringCodec(DidCodec):
    def __init__(self):
        pass

    def encode(self, hex_string: str) -> bytes:
        if not isinstance(hex_string, str):
            raise ValueError("AsciiCodec requires a string for encoding")

        return bytes.fromhex(hex_string)

    def decode(self, string_bin: bytes) -> str:
        return string_bin.hex()

    def __len__(self) -> int:
        raise DidCodec.ReadAllRemainingData
    

class RawBytesCodec(DidCodec):
    def __init__(self):
        pass

    def encode(self, data: bytes) -> bytes:
        return data

    def decode(self, data: bytes) -> bytes:
        return data

    def __len__(self) -> int:
        raise DidCodec.ReadAllRemainingData

class UdsUtils(UdsUtilsBase):
    data_link_layer: Union[IsoTpCommunicator, DoipCommunicator]
    attempts: int = Field(default=1, ge=1, description="Number of attempts to perform the UDS operation if no response was received")
    _crypto_utils: CryptoUtils = CryptoUtils()

    def setup(self) -> bool:
        """setup the library
        """
        return self.data_link_layer.open()
    
    def teardown(self):
        """Teardown the library
        """
        self.data_link_layer.close()
    
    def session(self, session: int, timeout: float = DEFAULT_UDS_OPERATION_TIMEOUT, standard_version: UdsStandardVersion = UdsStandardVersion.ISO_14229_2020) -> SessionControlResultData:
        """	Diagnostic Session Control

        Args:
            timeout (float): timeout for the UDS operation in seconds
            session (int): session to switch into
            standard_version (UdsStandardVersion, optional): the version of the UDS standard we are interacting with. Defaults to ISO_14229_2020.
            
        :raises RuntimeError: If failed to send the request
        :raises ValueError: If parameters are out of range, missing or wrong type
        :raises NoResponse: If no response was received
        :raises InvalidResponse: with invalid reason, if invalid response has received
        :raises NegativeResponse: with error code and code name, If negative response was received

        Returns:
            SessionControlResultData
        """
        request = DiagnosticSessionControl.make_request(session=session)
        response = self._send_and_read_response(request=request, timeout=timeout)   
        interpreted_response = DiagnosticSessionControl.interpret_response(response=response, standard_version=standard_version)
        return interpreted_response.service_data
    
    def transit_to_session(self, route_to_session: list[SESSION_ACCESS], timeout: float = DEFAULT_UDS_OPERATION_TIMEOUT, standard_version: UdsStandardVersion = UdsStandardVersion.ISO_14229_2020) -> bool:
        """Transit to the UDS session according to route

        Args:
            route_to_session (list[SESSION_ACCESS]): list of UDS SESSION_ACCESS objects to follow
            timeout (float): timeout for the UDS operation in seconds
            standard_version (UdsStandardVersion, optional): the version of the UDS standard we are interacting with. Defaults to ISO_14229_2020.

        Returns:
            bool: True if succeeded to transit to the session, False otherwise 
        """
        for session in route_to_session:
            try:    
                change_session_ret = self.session(session=session.id, timeout=timeout, standard_version=standard_version)
                if change_session_ret.session_echo != session.id:
                    self.logger.warning(f"Unexpected session ID echo, expected: {hex(session.id)}, got {hex(change_session_ret.session_echo)}")
                
                # try to elevate security access if algorithm is provided for this session
                if session.elevation_info and session.elevation_info.security_algorithm:
                    try:
                        self.security_access(security_algorithm=session.elevation_info.security_algorithm, timeout=timeout)
                    except Exception as ex:
                        self.logger.warning(f"Failed to get security access, continuing without. error: {ex}")

            except Exception as ex:
                self.logger.warning(f"Failed to switch to session: {hex(session.id)}, what: {ex}")
                return False

        return True
    
    def ecu_reset(self, reset_type: int, timeout: float = DEFAULT_UDS_OPERATION_TIMEOUT) -> bool:
        """The service "ECU reset" is used to restart the control unit (ECU)

        Args:
            timeout (float): timeout for the UDS operation in seconds
            reset_type (int): type of the reset (1: hard reset, 2: key Off-On Reset, 3: Soft Reset, .. more manufacture specific types may be supported)

        :raises RuntimeError: If failed to send the request
        :raises ValueError: If parameters are out of range, missing or wrong type
        :raises NoResponse: If no response was received
        :raises InvalidResponse: with invalid reason, if invalid response has received
        :raises NegativeResponse: with error code and code name, If negative response was received

        Returns:
            bool: True if ECU request was accepted, False otherwise.
        """
        request = ECUReset.make_request(reset_type=reset_type)
        response = self._send_and_read_response(request=request, timeout=timeout)
        interpreted_response = ECUReset.interpret_response(response=response)
        return interpreted_response.service_data.reset_type_echo == reset_type

    def read_did(self, didlist: Union[int, list[int]], timeout: float = DEFAULT_UDS_OPERATION_TIMEOUT) -> list[RdidDataTuple]:
        """	Read Data By Identifier

        Args:
            timeout (float): timeout for the UDS operation in seconds
            didlist (Union[int, list[int]]): List of data identifier to read.

        :raises RuntimeError: If failed to send the request
        :raises ValueError: If parameters are out of range, missing or wrong type
        :raises NoResponse: If no response was received
        :raises InvalidResponse: with invalid reason, if invalid response has received
        :raises NegativeResponse: with error code and code name, If negative response was received

        Returns:
            dict[int, str]: Dictionary mapping the DID (int) with the value returned
        """
        request = ReadDataByIdentifier.make_request(didlist=didlist, didconfig=None)
        response = self._send_and_read_response(request=request, timeout=timeout)
        return self._split_dids(didlist=didlist, data_bytes=response.data)

    def routine_control(self, routine_id: int, control_type: int, timeout: float = DEFAULT_UDS_OPERATION_TIMEOUT, data: Optional[bytes] = None) -> RoutingControlResponseData:
        """Sends a request for RoutineControl

        Args:
            timeout (float): timeout for the UDS operation in seconds
            routine_id (int): The routine ID
            control_type (int): Service subfunction
            data (Optional[bytes], optional): Optional additional data to provide to the server. Defaults to None.

        :raises RuntimeError: If failed to send the request
        :raises ValueError: If parameters are out of range, missing or wrong type
        :raises NoResponse: If no response was received
        :raises InvalidResponse: with invalid reason, if invalid response has received
        :raises NegativeResponse: with error code and code name, If negative response was received

        Returns:
            RoutingControlResponseData
        """
        request = RoutineControl.make_request(routine_id=routine_id, control_type=control_type, data=data)
        response = self._send_and_read_response(request=request, timeout=timeout)
        interpreted_response = RoutineControl.interpret_response(response=response)
        return interpreted_response.service_data

    def tester_present(self, timeout: float = DEFAULT_UDS_OPERATION_TIMEOUT) -> bool:
        """Sends a request for TesterPresent

        Args:
            timeout (float): timeout for the UDS operation in seconds

        :raises RuntimeError: If failed to send the request
        :raises ValueError: If parameters are out of range, missing or wrong type
        :raises NoResponse: If no response was received
        :raises InvalidResponse: with invalid reason, if invalid response has received
        :raises NegativeResponse: with error code and code name, If negative response was received

        Returns:
            bool: True if tester preset was accepted successfully. False otherwise
        """
        request = TesterPresent.make_request()
        response = self._send_and_read_response(request=request, timeout=timeout)
        interpreted_response = TesterPresent.interpret_response(response=response)
        return interpreted_response.service_data.subfunction_echo == 0

    def write_did(self, did: int, value: str | bytes, timeout: float = DEFAULT_UDS_OPERATION_TIMEOUT) -> bool:
        """Sends a request for WriteDataByIdentifier

        Args:
            timeout (float): timeout for the UDS operation in seconds
            did (int): The data identifier to write
            value (str): the value to write

        :raises RuntimeError: If failed to send the request
        :raises ValueError: If parameters are out of range, missing or wrong type
        :raises NoResponse: If no response was received
        :raises InvalidResponse: with invalid reason, if invalid response has received
        :raises NegativeResponse: with error code and code name, If negative response was received

        Returns:
            bool: True if WriteDataByIdentifier request sent successfully, False otherwise
        """
        if isinstance(value, str):
            codec = HexStringCodec()
        elif isinstance(value, bytes):
            codec = RawBytesCodec()
        else:
            raise ValueError(f"Value of type {type(value)} is not supported.")
        
        request = WriteDataByIdentifier.make_request(did=did, value=value, didconfig={did: codec})
        response = self._send_and_read_response(request=request, timeout=timeout)
        interpreted_response = WriteDataByIdentifier.interpret_response(response=response)
        return interpreted_response.service_data.did_echo == did
    
    def security_access(self, security_algorithm: Type[SECURITY_ALGORITHM_BASE], timeout: float = DEFAULT_UDS_OPERATION_TIMEOUT) -> bool:
        """Sends a request for SecurityAccess

        Args:
            timeout (float): timeout for the UDS operation in seconds
            security_algorithm (Type[SECURITY_ALGORITHM_BASE]): security algorithm to use for security access

        :raises RuntimeError: If failed to send the request
        :raises ValueError: If parameters are out of range, missing or wrong type
        :raises NoResponse: If no response was received
        :raises InvalidResponse: with invalid reason, if invalid response has received
        :raises NegativeResponse: with error code and code name, If negative response was received

        Returns:
            bool: True if security access was allowed to the requested level. False otherwise
        """
        request = SecurityAccess.make_request(level=security_algorithm.seed_subfunction,
                                                                mode=SecurityAccess.Mode.RequestSeed)
        response = self._send_and_read_response(request=request, timeout=timeout)
        interpreted_response = SecurityAccess.interpret_response(response=response,
                                                                                   mode=SecurityAccess.Mode.RequestSeed)
        
        if all(b == 0 for b in interpreted_response.service_data.seed):
            # all zero seed means that security level is already unlocked
            return True
        
        session_key: bytes = security_algorithm(interpreted_response.service_data.seed)
        request = SecurityAccess.make_request(level=security_algorithm.key_subfunction,
                                                                mode=SecurityAccess.Mode.SendKey,
                                                                data=session_key)
        response = self._send_and_read_response(request=request, timeout=timeout)
        interpreted_response = SecurityAccess.interpret_response(response=response,
                                                                                   mode=SecurityAccess.Mode.SendKey)
        
        return interpreted_response.service_data.security_level_echo == security_algorithm.key_subfunction

    def request_download(self, address: int, memorysize: int, enc_comp: int = 0, address_format: int = 4,
                         memorysize_format: int = 4, timeout: float = DEFAULT_UDS_OPERATION_TIMEOUT) -> int:
        """Send a Request Download UDS message

        Args:
            timeout (float, optional): Timeout for the UDS operation in seconds. Defaults to DEFAULT_UDS_OPERATION_TIMEOUT.
            address (int): Block ID or address of the relevant memory region to update.
            memorysize (int): Size of the memory region to update.
            enc_comp (int, optional): Encription and Compression info. Defaults to 0 (no encription and no compression).
            address_format (int, optional): Length in bytes of the Address field. Defaults to 4.
            memorysize_format (int, optional): Length in bytes of the Size field. Defaults to 4.

        :raises RuntimeError: If failed to send the request
        :raises ValueError: If parameters are out of range, missing or wrong type
        :raises NoResponse: If no response was received
        :raises InvalidResponse: with invalid reason, if invalid response has received
        :raises NegativeResponse: with error code and code name, If negative response was received

        Returns:
            int: Maximum block length for following transfer data.
        """
        memory_location = MemoryLocation(
            address=address,
            memorysize=memorysize,
            address_format=8*address_format,
            memorysize_format=8*memorysize_format,
        )

        dfi = DataFormatIdentifier.from_byte(enc_comp)

        request: Request = RequestDownload.make_request(memory_location, dfi)
        response = self._send_and_read_response(request=request, timeout=timeout)
        interpreted_response = RequestDownload.interpret_response(response=response)
        return interpreted_response.service_data.max_length

    def transfer_data(self, seq: int, data: bytes, timeout: float = DEFAULT_UDS_OPERATION_TIMEOUT) -> None:
        """Transfer a block of data as part of Upload or Download session

        Args:
            timeout (float, optional): Timeout for the UDS operation in seconds. Defaults to DEFAULT_UDS_OPERATION_TIMEOUT.
            seq (int): Sequence nuber of the current TransferData.
            data (bytes): Data to be transfered.

        :raises RuntimeError: If failed to send the request
        :raises ValueError: If parameters are out of range, missing or wrong type
        :raises NoResponse: If no response was received
        :raises InvalidResponse: with invalid reason, if invalid response has received
        :raises NegativeResponse: with error code and code name, If negative response was received
        """

        request: Request = TransferData.make_request(sequence_number=seq, data=data)
        response = self._send_and_read_response(request=request, timeout=timeout)
        interpreted_response = TransferData.interpret_response(response=response)
        resp_seq = interpreted_response.service_data.sequence_number_echo
        if resp_seq != seq:
            raise InvalidResponse(f"Unexpected sequence number response {resp_seq}, expected {seq}.")

    def transfer_exit(self, data: bytes | None = None, timeout: float = DEFAULT_UDS_OPERATION_TIMEOUT) -> bytes:
        """Finish transfer session

        Args:
            data (bytes, optional): Additional optional data to send to the server
            timeout (float, optional): Timeout for the UDS operation in seconds. Defaults to DEFAULT_UDS_OPERATION_TIMEOUT.

        :raises RuntimeError: If failed to send the request
        :raises ValueError: If parameters are out of range, missing or wrong type
        :raises NoResponse: If no response was received
        :raises InvalidResponse: with invalid reason, if invalid response has received
        :raises NegativeResponse: with error code and code name, If negative response was received

        Returns:
            bytes: The parameter records received from the transfer exit response.
        """
        request: Request = RequestTransferExit.make_request(data=data)
        response = self._send_and_read_response(request=request, timeout=timeout)
        interpreted_response = RequestTransferExit.interpret_response(response=response)
        return interpreted_response.service_data.parameter_records

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
            dtc (Optional[int], optional): A DTC mask used to filter DTC. Defaults to None.
            snapshot_record_number (Optional[int], optional): Snapshot record number. Defaults to None.
            extended_data_record_number (Optional[int], optional): Extended data record number. Defaults to None.
            memory_selection (Optional[int], optional): Memory selection for user defined memory DTC. Defaults to None.
            timeout (float, optional): Timeout for the UDS operation in seconds. Defaults to DEFAULT_UDS_OPERATION_TIMEOUT.
            standard_version (UdsStandardVersion, optional): the version of the UDS standard we are interacting with. Defaults to ISO_14229_2020.

        :raises RuntimeError: If failed to send the request
        :raises ValueError: If parameters are out of range, missing or wrong type
        :raises NoResponse: If no response was received
        :raises InvalidResponse: with invalid reason, if invalid response has received
        :raises NegativeResponse: with error code and code name, If negative response was received

        Returns:
            DtcInformationData: The DTC information response data containing the requested DTC information
        """
        request = ReadDTCInformation.make_request(
            subfunction=subfunction,
            status_mask=status_mask,
            severity_mask=severity_mask,
            dtc=dtc,
            snapshot_record_number=snapshot_record_number,
            extended_data_record_number=extended_data_record_number,
            memory_selection=memory_selection,
            standard_version=standard_version
        )
        response = self._send_and_read_response(request=request, timeout=timeout)
        interpreted_response = ReadDTCInformation.interpret_response(response=response, subfunction=subfunction, standard_version=standard_version)
        return interpreted_response.service_data
    
    def clear_diagnostic_information(self, group: int = 0xFFFFFF, memory_selection: Optional[int] = None, timeout: float = DEFAULT_UDS_OPERATION_TIMEOUT, standard_version: UdsStandardVersion = UdsStandardVersion.ISO_14229_2020) -> bool:
        """Clear Diagnostic Information service (0x14)

        Args:
            group (int, optional): DTC mask ranging from 0 to 0xFFFFFF. 0xFFFFFF means all DTCs. Defaults to 0xFFFFFF.
            memory_selection (Optional[int], optional): Number identifying the respective DTC memory. Only supported in ISO-14229-1:2020 and above. Defaults to None.
            timeout (float, optional): Timeout for the UDS operation in seconds. Defaults to DEFAULT_UDS_OPERATION_TIMEOUT.
            standard_version (UdsStandardVersion, optional): the version of the UDS standard we are interacting with. Defaults to ISO_14229_2020.

        :raises RuntimeError: If failed to send the request
        :raises ValueError: If parameters are out of range, missing or wrong type
        :raises NoResponse: If no response was received
        :raises InvalidResponse: with invalid reason, if invalid response has received
        :raises NegativeResponse: with error code and code name, If negative response was received

        Returns:
            bool: True if the clear operation was successful, False otherwise
        """
        request = ClearDiagnosticInformation.make_request(group=group, memory_selection=memory_selection, standard_version=standard_version)
        response = self._send_and_read_response(request=request, timeout=timeout)
        ClearDiagnosticInformation.interpret_response(response=response)
        return True  # If we get here, the operation was successful since no negative response was raised

    def raw_uds_service(self, sid: UdsSid, timeout: float = DEFAULT_UDS_OPERATION_TIMEOUT, sub_function: Optional[int] = None, data: Optional[bytes] = None) -> RawUdsResponse:
        """sends raw UDS service request and reads response

        Args:
            sid (UdsSid): Service ID of the request
            timeout (float): timeout for the UDS operation in seconds
            sub_function (Optional[int], optional): The service subfunction. Defaults to None.
            data (Optional[bytes], optional): The service data. Defaults to None.

        :raises RuntimeError: If failed to send the request
        :raises ValueError: If parameters are out of range, missing or wrong type
        :raises NoResponse: If no response was received
        :raises InvalidResponse: with invalid reason, if invalid response has received

        Returns:
            RawUdsResponse: Raw UdsResponse
        """
        if sub_function is not None:
            service = RAW_SERVICES_WITH_SUB_FUNC[sid]
        else:
            service = RAW_SERVICES_WITHOUT_SUB_FUNC[sid]
        request = Request(service=service, subfunction=sub_function, data=data)
        return self._send_and_read_raw_response(request=request, timeout=timeout)
    
    def authentication(self, 
                       params: Type[AuthenticationParamsBase],
                       timeout: float = DEFAULT_UDS_OPERATION_TIMEOUT) -> AuthenticationReturnParameter:
        """Initiate UDS Authentication service sequence 

        Args:
            params (Type[AuthenticationParamsBase]): Set of parameters defined for the desired authentication task
            timeout (float): timeout for the UDS operation in seconds

        :raises NotImplementedError: for operations that are not supported yet
        :raises RuntimeError: If failed to send the request
        :raises ValueError: If parameters are out of range, missing or wrong type
        :raises NoResponse: If no response was received
        :raises InvalidResponse: with invalid reason, if invalid response has received

        Returns:
            AuthenticationReturnParameter: The results code of the authentication action
        """
        match params.authentication_action():
            case AuthenticationAction.AuthenticationConfiguration:
                return self._authentication_configuration(timeout)
            case AuthenticationAction.PKI_CertificateExchangeUnidirectional:
                return self._authentication_uni_certificate_exchange(
                    params=params,
                    timeout=timeout
                    )
            case AuthenticationAction.PKI_CertificateExchangeBidirectional:
                raise NotImplementedError("PKI_CertificateExchangeBidirectional is not implemented yet")
            case AuthenticationAction.ChallengeResponse:
                raise NotImplementedError("ChallengeResponse is not implemented yet")
            case AuthenticationAction.DeAuthenticate:
                return self._authentication_deauthenticate(timeout)
            case AuthenticationAction.TransmitCertificate:
                return self._authentication_transmit_certificate(
                    params=params,
                    timeout=timeout
                )
            case _:
                raise ValueError(f"invalid authentication action received: {params.authentication_action()}")
            
    def _authentication_transmit_certificate(
            self,
            params: TransmitCertificateParams,
            timeout: float
            ) -> AuthenticationReturnParameter:
        request = Authentication.make_request(
            authentication_task=Authentication.AuthenticationTask.transmitCertificate,
            certificate_evaluation_id=params.certificate_evaluation_id,
            certificate_data=params.certificate_data
            )
        response = self._send_and_read_response(request=request, timeout=timeout)
        interpreted_response = Authentication.interpret_response(response)
        return AuthenticationReturnParameter(interpreted_response.service_data.return_value)

    def _authentication_deauthenticate(self, timeout: float) -> AuthenticationReturnParameter:
        request = Authentication.make_request(Authentication.AuthenticationTask.deAuthenticate)
        response = self._send_and_read_response(request=request, timeout=timeout)
        interpreted_response = Authentication.interpret_response(response)
        return AuthenticationReturnParameter(interpreted_response.service_data.return_value)
            
    def _authentication_configuration(self, timeout: float) -> AuthenticationReturnParameter:
        request = Authentication.make_request(Authentication.AuthenticationTask.authenticationConfiguration)
        response = self._send_and_read_response(request=request, timeout=timeout)
        interpreted_response = Authentication.interpret_response(response)
        return AuthenticationReturnParameter(interpreted_response.service_data.return_value)
    
    def _authentication_uni_certificate_exchange(
            self, 
            params: UnidirectionalAPCEParams,
            timeout: float) -> AuthenticationReturnParameter:
        # send certificate
        request = Authentication.make_request(authentication_task=Authentication.AuthenticationTask.verifyCertificateUnidirectional,
                                              communication_configuration=params.communication_configuration,
                                              certificate_client=params.certificate_client)
        response = self._send_and_read_response(request=request, timeout=timeout)
        interpreted_response = Authentication.interpret_response(response)
        if not interpreted_response.service_data.challenge_server:
            raise InvalidResponse("Expected challenge from server but none received")
        
        if interpreted_response.service_data.ephemeral_public_key_server:
            raise NotImplementedError("Session key establishment is not supported yet")
        
        # sign challenge
        sig_data = self._crypto_utils.sign_data(
            private_key_der=params.private_key_der,
            data=interpreted_response.service_data.challenge_server,
            hash_alg=params.hash_algorithm,
            padding=params.asym_padding_type
        )

        # send proof of ownership
        request = Authentication.make_request(authentication_task=Authentication.AuthenticationTask.proofOfOwnership,
                                              proof_of_ownership_client=sig_data)
        
        response = self._send_and_read_response(request=request, timeout=timeout)
        interpreted_response = Authentication.interpret_response(response)

        return AuthenticationReturnParameter(interpreted_response.service_data.return_value)

    def _send_and_read_response(self, request: Request, timeout: float = DEFAULT_UDS_OPERATION_TIMEOUT) -> RawUdsResponse:
        response = self._send_and_read_raw_response(request=request, timeout=timeout)
        
        if not response.positive:
            raise NegativeResponse(code=response.code, code_name=response.code_name)
        
        return response
    
    def _send_and_read_raw_response(self, request: Request, timeout: float = DEFAULT_UDS_OPERATION_TIMEOUT) -> RawUdsResponse:
        raw_response = None
        for i in range(self.attempts):
            sent_bytes = self.data_link_layer.send(data=request.get_payload(), timeout=timeout)
            if sent_bytes < len(request.get_payload()):
                self.logger.error("Failed to send request")
                raise RuntimeError("Failed to send request")
            
            start = time.time()
            while True:
                now = time.time()
                if (now - start) > timeout:
                    self.logger.debug(f"Timeout reading response for request with SID: {hex(request.service.request_id())}, attempt {i}")
                    break

                raw_response = self.data_link_layer.recv(recv_timeout=timeout)

                if not raw_response:
                    self.logger.debug(f"No response for request with SID: {hex(request.service.request_id())}, attempt {i}")
                    break

                response = RawUdsResponse.from_payload(payload=raw_response)
                if not response.valid:
                    raise InvalidResponse(invalid_reason=response.invalid_reason)
                
                if response.service.response_id() != request.service.response_id():
                    self.logger.debug(f"Got unexpected response: {response.service.get_name()}, request was {request.service.get_name()}, discarding and trying to receive again")
                    raw_response = None
                    continue
                
                if not response.positive and response.code == UdsResponseCode.RequestCorrectlyReceived_ResponsePending:
                    self.logger.debug(f"Got error: {response.code_name}, trying to receive again")
                    continue
                else:
                    return response
            

        if not raw_response:
            raise NoResponse
        
        return response
    
    def _split_dids(self, didlist: Union[int, list[int]], data_bytes: bytes) -> list[RdidDataTuple]:  
        if isinstance(didlist, int):  
            didlist = [didlist]  
    
        dids_values = []  
        next_position = 0
    
        for i, curr_did_int in enumerate(didlist):
            curr_position = data_bytes.find(curr_did_int.to_bytes(length=2, byteorder='big')) if i == 0 else next_position  
            if curr_position == -1:  
                self.logger.warning(f"Unexpected DID: {hex(curr_did_int)}, not found in the data.")  
                continue  
            if i < len(didlist) - 1:  # If it's not the last id  
                next_position = data_bytes.find(didlist[i + 1].to_bytes(length=2, byteorder='big'), curr_position + 2)  
                if next_position == -1:  
                    data = data_bytes[curr_position + 2:]
                else:
                    data = data_bytes[curr_position + 2: next_position]  
            else:  # If it's the last id  
                data = data_bytes[curr_position + 2:]  
    
            dids_values.append(RdidDataTuple(did=curr_did_int, data=data.hex()))  
    
        return dids_values  

    def __str__(self):
        return str(self.data_link_layer)