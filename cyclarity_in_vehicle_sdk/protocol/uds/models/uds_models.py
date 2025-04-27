from abc import ABC, abstractmethod
from enum import Enum, IntEnum, auto
import inspect
import struct
from typing import Literal, Optional, Type, Union
from cyclarity_in_vehicle_sdk.utils.crypto.models import AsymmetricPaddingType, HashingAlgorithm
from cyclarity_in_vehicle_sdk.utils.custom_types.hexbytes import HexBytes
from cyclarity_sdk.sdk_models.models import CyclarityFile
from pydantic import BaseModel, Field
from cyclarity_in_vehicle_sdk.utils.custom_types.enum_by_name import pydantic_enum_by_name


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


@pydantic_enum_by_name
class AuthenticationAction(Enum):
    """Types of authentication actions
    """
    PKI_CertificateExchangeUnidirectional = auto()
    PKI_CertificateExchangeBidirectional = auto()
    ChallengeResponse = auto()
    AuthenticationConfiguration = auto()
    DeAuthenticate = auto()
    TransmitCertificate = auto()

class AuthenticationParamsBase(BaseModel):
    @abstractmethod
    def authentication_action(self) -> AuthenticationAction:
        raise NotImplementedError
    
    @classmethod  
    def get_non_abstract_subclasses(cls) -> list[Type]:  
        subclasses = []  
  
        for subclass in cls.__subclasses__():  
            # Check if the subclass itself has any subclasses  
            subclasses.extend(subclass.get_non_abstract_subclasses())  
              
            # Check if the subclass is non-abstract  
            if not inspect.isabstract(subclass):  
                subclasses.append(subclass)  
  
        return subclasses  
    

class BaseAPCEParams(AuthenticationParamsBase):
    """Base class defining parameters for UDS Authentication based on asymmetric public certificate exchange
    """
    private_key_der: Union[HexBytes, CyclarityFile] = Field(description="The private key for authentication in DER format")
    certificate_client: Union[HexBytes, CyclarityFile] = Field(description="The client's certificate to send to the server for authentication")
    asym_padding_type: AsymmetricPaddingType = Field(description="The padding type to use in signature creation for challenge signing")
    hash_algorithm: HashingAlgorithm = Field(description="The hashing algorithm to use in signature creation for challenge signing")
    communication_configuration: int = Field(default=0,
                                             ge=0,
                                             le=255,
                                             description=("Configuration information about how to proceed with security"
                                             " in further diagnostic communication after the Authentication (vehicle manufacturer specific)"))


class UnidirectionalAPCEParams(BaseAPCEParams):
    """Model defining the parameters for UDS Authentication based on unidirectional asymmetric public certificate exchange
    """
    param_type: Literal["UnidirectionalAPCEParams"] = "UnidirectionalAPCEParams"
    def authentication_action(self) -> AuthenticationAction:
        return AuthenticationAction.PKI_CertificateExchangeUnidirectional


class AuthenticationConfigurationParams(AuthenticationParamsBase):
    """Model for the parameters of the AuthenticationConfiguration action
    """
    param_type: Literal["AuthenticationConfigurationParams"] = "AuthenticationConfigurationParams"
    def authentication_action(self) -> AuthenticationAction:
        return AuthenticationAction.AuthenticationConfiguration


class DeAuthenticateParams(AuthenticationParamsBase):
    """Model for the parameters of the DeAuthenticate action
    """
    param_type: Literal["DeAuthenticateParams"] = "DeAuthenticateParams"
    def authentication_action(self) -> AuthenticationAction:
        return AuthenticationAction.DeAuthenticate


class TransmitCertificateParams(AuthenticationParamsBase):
    """Model defining the parameters for UDS Authentication - Transmit Certificate
    """
    param_type: Literal["TransmitCertificateParams"] = "TransmitCertificateParams"
    certificate_evaluation_id: int = Field(ge=0,
                                           le=0xffff,
                                           description=("Optional unique ID to identify the evaluation type "
                                           "of the transmitted certificate"))
    certificate_data: HexBytes = Field(description="The Certificate to verify")

    def authentication_action(self) -> AuthenticationAction:
        return AuthenticationAction.TransmitCertificate


@pydantic_enum_by_name
class AuthenticationReturnParameter(IntEnum):
    """Model defining the authentication return codes
    """
    RequestAccepted = 0x00
    GeneralReject = 0x01
    AuthenticationConfiguration_APCE = 0x02
    AuthenticationConfiguration_ACR_with_asymmetric_cryptography = 0x03
    AuthenticationConfiguration_ACR_with_symmetric_cryptography = 0x04
    DeAuthentication_successful = 0x10
    CertificateVerified_OwnershipVerificationNecessary = 0x11
    OwnershipVerified_AuthenticationComplete = 0x12
    CertificateVerified = 0x13


@pydantic_enum_by_name
class UdsStandardVersion(IntEnum):
    """Model defining the UDS standard versions
    """
    ISO_14229_2006 = 2006
    ISO_14229_2013 = 2013
    ISO_14229_2020 = 2020


class SECURITY_ALGORITHM_BASE(BaseModel, ABC):
    """Base model for security access algorithms
    """
    seed_subfunction: Optional[int] = Field(default=None, description="The subfunction for the get seed operation")
    key_subfunction: Optional[int] = Field(default=None, description="The subfunction for the send key operation")

    @abstractmethod
    def __call__(self, seed: bytes) -> bytes:
        raise NotImplementedError


class SECURITY_ALGORITHM_XOR(SECURITY_ALGORITHM_BASE):
    """Model for XOR based security access
    """
    xor_val: int = Field(description="Integer value to XOR the seed with for security key generation")
    def __call__(self, seed: bytes) -> bytes:
        """Callable to generate the key out of a seed, by XORing the seed with the predefined value 

        Args:
            seed (bytes): the seed

        Returns:
            bytes: the generated key
        """
        seed_int = int.from_bytes(seed, byteorder='big')
        key_int = seed_int ^ self.xor_val
        return struct.pack('>L',key_int)

class SECURITY_ALGORITHM_PIN(SECURITY_ALGORITHM_BASE):
    """Model for PIN based security access
    """
    pin: int = Field(description="Integer value to be added to the seed for security key generation")
    def __call__(self, seed: bytes) -> bytes:
        """Callable to generate the key out of a seed, by adding a predefined pin value with the seed

        Args:
            seed (bytes): the seed

        Returns:
            bytes: the generated key
        """
        seed_int = int.from_bytes(seed, byteorder='big')
        seed_int += self.pin
        return struct.pack('>L',seed_int)
    
SecurityAlgorithm = Union[SECURITY_ALGORITHM_XOR, 
                          SECURITY_ALGORITHM_PIN]

class ELEVATION_INFO(BaseModel):
    """Model for defining the needed elevation information for a UDS session
    """
    need_elevation: Optional[bool] = Field(default=None, description="Whether this session requires elevation")
    security_algorithm: Optional[SecurityAlgorithm] = Field(default=None, description="The security elevation algorithm")
    def __str__(self):
        return f"{'Needs elevation' if self.need_elevation else ''}, {'Elevation Callback is available' if self.security_algorithm else ''}"

class ERROR_CODE_AND_NAME(BaseModel):
    """Model defining the error code and its name
    """
    code: int = Field(description="Error code number")
    code_name: str = Field(description="Error code name")
    def __str__(self):
        return f"({hex(self.code)}) {self.code_name}"

class SERVICE_INFO(BaseModel):
    """Model containing information regarding a UDS service
    """
    sid: int = Field(description="The SID of the UDS service")
    name: str = Field(description="The name of the UDS service")
    error: Optional[ERROR_CODE_AND_NAME] = Field(default=None, description="The error code if exists")
    accessible: bool = Field(default=False, description="Whether this UDS service is accessible")
    def __str__(self):
        return (f"{self.name} ({hex(self.sid)})"
                f"{', Accessible' if self.accessible else ', Inaccessible'}"
                f"{', Error: ' + str(self.error) if self.error else ''}")

class DID_INFO(BaseModel):
    """Model containing information regarding a UDS Data Identifier
    """
    did: int
    name: Optional[str] = None
    accessible: bool
    current_data: Optional[str] = None
    maybe_supported_error: Optional[ERROR_CODE_AND_NAME] = Field(default=None, 
                                                                   description="The error code if there is uncertainty that this DID is supported")
    def __str__(self):
        return (f"DID {hex(self.did)} ({self.name if self.name else 'Unknown'}), "  
                f"{'Accessible' if self.accessible else 'Inaccessible'}"  
                f"{(', Maybe supported error: ' + str(self.maybe_supported_error)) if self.maybe_supported_error else ''}, "  
                f"{('Data (len=' + str(round(len(self.current_data) / 2)) + '): ' + self.current_data[:20]) if self.current_data else ''}"  
)  

class ROUTINE_OPERATION_INFO(BaseModel):
    """Model containing information regarding a UDS routine subfunction
    """
    control_type: int
    accessible: bool
    maybe_supported_error: Optional[ERROR_CODE_AND_NAME] = Field(default=None,
                                                                 description="The error code if there is uncertainty that this routine control type is supported")
    routine_status_record: Optional[str] = Field(default=None,
                                                 description="Additional data associated with the response.")
    def __str__(self):
        return (f"Routine control type {hex(self.control_type)}"
                f"{', Accessible' if self.accessible else ', Inaccessible'}"
                f"{(', Maybe supported error: ' + str(self.maybe_supported_error)) if self.maybe_supported_error else ''}"  
                f"{(', Routine status record (len=' + str(round(len(self.routine_status_record) / 2)) + '): ' + self.routine_status_record[:20]) if self.routine_status_record else ''}"  
                )

class ROUTINE_INFO(BaseModel):
    """Model containing information regarding a UDS routine
    """
    routine_id: int
    operations: list[ROUTINE_OPERATION_INFO]
    def __str__(self):
        operations_str = '\n'.join(str(operation) for operation in self.operations)
        return (f"Routine ID {hex(self.routine_id)}, Sub Operations:\n"
                f"{operations_str}\n")

class SESSION_ACCESS(BaseModel):
    """Model containing information regarding how to access a UDS session
    """
    id: int = Field(description="ID of this UDS session")
    elevation_info: Optional[ELEVATION_INFO] = Field(default=None, description="Elevation info for this UDS session, if needed")

class SESSION_INFO(BaseModel):
    """Model containing information regarding a UDS session
    """
    accessible: bool = Field(default=False, description="Whether this UDS session is accessible")
    elevation_info: Optional[ELEVATION_INFO] = Field(default=None, description="Elevation info for this UDS session")
    route_to_session: list[SESSION_ACCESS] = Field(default=[], description="The UDS session route to reach this session")

DEFAULT_SESSION = SESSION_INFO(route_to_session=[SESSION_ACCESS(id=1)])