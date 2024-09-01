from ipaddress import IPv6Address
from typing import Optional
from enum import IntFlag

from pydantic import BaseModel, Field

from clarity.common.models import SCAN_TRACE
import py_pcapplusplus as pypcap

L4_PROTO_TCP = 0x6
L4_PROTO_UDP = 0x11
TEMP_LISTEN_PORT = 42700


class SOMEIP_EVTGROUP_INFO(BaseModel):
    initial_data: Optional[str] = None
    trace: Optional[SCAN_TRACE] = None


class SOMEIP_METHOD_INFO(BaseModel):
    trace: Optional[SCAN_TRACE] = None


class SOMEIP_SERVICE_INFO(BaseModel):
    inst_id: int
    major_ver: int
    minor_ver: int
    ttl: int
    endpoint_addr: str
    port: int
    port_type: pypcap.SomeIpSdProtocolType
    trace: Optional[SCAN_TRACE] = None


class SOMEIP_TARGET(BaseModel):
    target_ip: IPv6Address
    source_ip: str
    source_port: int
    destination_port: int


class SOMEIP_INFO(BaseModel):
    someip_targets: list[SOMEIP_TARGET] = Field(default_factory=list[SOMEIP_TARGET])

class SomeIpSdOptionFlags(IntFlag):
    Reboot = 0x80
    Unicast = 0x40 
    ExplicitInitialData = 0x20