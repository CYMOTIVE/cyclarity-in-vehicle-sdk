from abc import ABC, abstractmethod
import struct
from typing import Optional

from pydantic import BaseModel, Field

class SECURITY_ALGORITHM_BASE(BaseModel, ABC):
    seed_subfunction: Optional[int] = None
    key_subfunction: Optional[int] = None

    @abstractmethod
    def __call__(self, seed: bytes) -> bytes:
        raise NotImplementedError


class SECURITY_ALGORITHM_XOR(SECURITY_ALGORITHM_BASE):
    xor_val: int
    def __call__(self, seed: bytes) -> bytes:
        seed_int = int.from_bytes(seed, byteorder='big')
        key_int = seed_int ^ self.xor_val
        return struct.pack('>L',key_int)

class SECURITY_ALGORITHM_PIN(SECURITY_ALGORITHM_BASE):
    pin: int
    def __call__(self, seed: bytes) -> bytes:
        seed_int = int.from_bytes(seed, byteorder='big')
        seed_int += self.pin
        return struct.pack('>L',seed_int)

class ELEVATION_INFO(BaseModel):
    need_elevation: Optional[bool] = None
    security_algorithm: Optional[SECURITY_ALGORITHM_BASE] = None
    def __str__(self):
        return f"{'Needs elevation' if self.need_elevation else ''}, {'Elevation Callback is available' if self.security_algorithm else ''}"


class SERVICE_INFO(BaseModel):
    name: str = str()
    supported: bool = False
    maybe_supported_error: Optional[str] = None
    elevation_info: Optional[ELEVATION_INFO] = None


class PERMISSION_INFO(BaseModel):
    accessible: bool = False
    elevation_info: ELEVATION_INFO = Field(default_factory=ELEVATION_INFO)
    maybe_supported_error: Optional[str] = None


class DID_INFO(BaseModel):
    read_permission: Optional[PERMISSION_INFO] = None
    write_permission: Optional[PERMISSION_INFO] = None
    current_data: Optional[str] = None


class ROUTINE_INFO(BaseModel):
    operations: dict[int, PERMISSION_INFO] = Field(
        default_factory=dict[int, PERMISSION_INFO]
    )


class SESSION_INFO(BaseModel):
    accessible: bool = False
    elevation_info: ELEVATION_INFO = Field(default_factory=ELEVATION_INFO)
    route_to_session: list[int] = []

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
