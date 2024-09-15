from enum import Enum
from typing import Callable, Literal, Optional, Union

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
    seed_subfunction: Optional[int] = None
    algorithm_cb: Optional[Callable[[bytes], bytes]] = None
    def __str__(self):
        return f"{'Needs elevation' if self.need_elevation else ''}, {'Elevation Callback is available' if self.algorithm_cb else ''}"


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
