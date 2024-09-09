from enum import Enum
from typing import Literal, Optional, Union

from pydantic import BaseModel, Field


# UDS INFO
class ElevationAlgorithm(str, Enum):
    UNKNOWN = "UNKNOWN"
    SA2 = "SA2"
    PIN = "PIN"


class SECURITY_ALGORITHM_BASE(BaseModel):
    algorithm_type: Literal[ElevationAlgorithm.UNKNOWN] = ElevationAlgorithm.UNKNOWN
    seed_request: Optional[int] = None
    key_response: Optional[int] = None


class SECURITY_ALGORITHM_PIN(SECURITY_ALGORITHM_BASE):
    algorithm_type: Literal[ElevationAlgorithm.PIN] = ElevationAlgorithm.PIN
    pin: Optional[int] = None


class ELEVATION_INFO(BaseModel):
    need_elevation: Optional[bool] = None
    algorithm: Union[SECURITY_ALGORITHM_PIN, SECURITY_ALGORITHM_BASE] = Field(
        default_factory=SECURITY_ALGORITHM_BASE, discriminator="algorithm_type"
    )
    def __str__(self):
        return "Needs elevation" if self.need_elevation else ""


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


class OPEN_SERVICE(BaseModel):
    sid: int


class SESSION_TRANSPOSITION(BaseModel):
    sess: int


class SESSION_INFO(BaseModel):
    accessible: bool = False
    elevation_info: ELEVATION_INFO = Field(default_factory=ELEVATION_INFO)
    prev_sessions: list[SESSION_TRANSPOSITION] = Field(
        default_factory=list[SESSION_TRANSPOSITION]
    )
    open_services: list[OPEN_SERVICE] = Field(default_factory=list[OPEN_SERVICE])
    dids: dict[int, DID_INFO] = Field(default_factory=dict[int, DID_INFO])
    routines: dict[int, ROUTINE_INFO] = Field(default_factory=dict[int, ROUTINE_INFO])


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
