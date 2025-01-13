from ipaddress import IPv6Address
from typing import Optional
from enum import IntFlag

from pydantic import BaseModel, Field, IPvAnyAddress

import py_pcapplusplus as pypcap

L4_PROTO_TCP = 0x6
L4_PROTO_UDP = 0x11
TEMP_LISTEN_PORT = 42700


class SOMEIP_EVTGROUP_INFO(BaseModel):
    initial_data: Optional[str] = None


class SOMEIP_METHOD_INFO(BaseModel):
    pass

class SOMEIP_ENDPOINT_OPTION(BaseModel):
    endpoint_addr: IPvAnyAddress
    port: int
    port_type: pypcap.SomeIpSdProtocolType

class SOMEIP_SERVICE_INFO(BaseModel):
    inst_id: int
    major_ver: int
    minor_ver: int
    ttl: int
    endpoints: list[SOMEIP_ENDPOINT_OPTION] = []


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