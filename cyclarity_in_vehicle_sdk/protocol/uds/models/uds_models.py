from abc import ABC, abstractmethod
from enum import IntEnum
import struct
from typing import Optional, Union
from pydantic import BaseModel, Field
from cyclarity_in_vehicle_sdk.utils.custom_types.enum_by_name import pydantic_enum_by_name


@pydantic_enum_by_name
class UdsStandardVersion(IntEnum):
    ISO_14229_2006 = 2006
    ISO_14229_2013 = 2013
    ISO_14229_2020 = 2020


class SECURITY_ALGORITHM_BASE(BaseModel, ABC):
    seed_subfunction: Optional[int] = Field(default=None, description="The subfunction for the get seed operation")
    key_subfunction: Optional[int] = Field(default=None, description="The subfunction for the send key operation")

    @abstractmethod
    def __call__(self, seed: bytes) -> bytes:
        raise NotImplementedError


class SECURITY_ALGORITHM_XOR(SECURITY_ALGORITHM_BASE):
    xor_val: int = Field(description="Integer value to XOR the seed with for security key generation")
    def __call__(self, seed: bytes) -> bytes:
        seed_int = int.from_bytes(seed, byteorder='big')
        key_int = seed_int ^ self.xor_val
        return struct.pack('>L',key_int)

class SECURITY_ALGORITHM_PIN(SECURITY_ALGORITHM_BASE):
    pin: int = Field(description="Integer value to be added to the seed for security key generation")
    def __call__(self, seed: bytes) -> bytes:
        seed_int = int.from_bytes(seed, byteorder='big')
        seed_int += self.pin
        return struct.pack('>L',seed_int)
    
SecurityAlgorithm = Union[SECURITY_ALGORITHM_XOR, 
                          SECURITY_ALGORITHM_PIN]

class ELEVATION_INFO(BaseModel):
    need_elevation: Optional[bool] = Field(default=None, description="Whether this session requires elevation")
    security_algorithm: Optional[SecurityAlgorithm] = Field(default=None, description="The security elevation algorithm")
    def __str__(self):
        return f"{'Needs elevation' if self.need_elevation else ''}, {'Elevation Callback is available' if self.security_algorithm else ''}"

class ERROR_CODE_AND_NAME(BaseModel):
    code: int = Field(description="Error code number")
    code_name: str = Field(description="Error code name")
    def __str__(self):
        return f"({hex(self.code)}) {self.code_name}"

class SERVICE_INFO(BaseModel):
    sid: int = Field(description="The SID of the UDS service")
    name: str = Field(description="The name of the UDS service")
    error: Optional[ERROR_CODE_AND_NAME] = Field(default=None, description="The error code if exists")
    accessible: bool = Field(default=False, description="Whether this UDS service is accessible")
    def __str__(self):
        return (f"{self.name} ({hex(self.sid)})"
                f"{', Accessible' if self.accessible else ', Inaccessible'}"
                f"{', Error: ' + str(self.error) if self.error else ''}")

class PERMISSION_INFO(BaseModel):
    accessible: bool = False
    elevation_info: ELEVATION_INFO = Field(default_factory=ELEVATION_INFO)
    maybe_supported_error: Optional[str] = None


class DID_INFO(BaseModel):
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
    routine_id: int
    operations: list[ROUTINE_OPERATION_INFO]
    def __str__(self):
        operations_str = '\n'.join(str(operation) for operation in self.operations)
        return (f"Routine ID {hex(self.routine_id)}, Sub Operations:\n"
                f"{operations_str}\n")

class SESSION_ACCESS(BaseModel):
    id: int = Field(description="ID of this UDS session")
    elevation_info: Optional[ELEVATION_INFO] = Field(default=None, description="Elevation info for this UDS session, if needed")

class SESSION_INFO(BaseModel):
    accessible: bool = Field(default=False, description="Whether this UDS session is accessible")
    elevation_info: Optional[ELEVATION_INFO] = Field(default=None, description="Elevation info for this UDS session")
    route_to_session: list[SESSION_ACCESS] = Field(default=[], description="The UDS session route to reach this session")

class UDS_INFO(BaseModel):
    open_sessions: dict[int, SESSION_INFO] = Field(
        default_factory=dict[int, SESSION_INFO]
    )
    services_info: dict[int, SERVICE_INFO] = Field(
        default_factory=dict[int, SERVICE_INFO]
    )

    def get_inner_scope(self, session=None, *args, **kwargs):
        if session is None:
            return ""

        if session not in self.open_sessions.keys():
            self.open_sessions[session] = SESSION_INFO()

        return f".open_sessions[{session}]"
