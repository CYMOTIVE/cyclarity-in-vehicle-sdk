from ipaddress import IPv6Address
from typing import Optional
from enum import IntFlag
from pydantic import BaseModel, Field, IPvAnyAddress
from cyclarity_in_vehicle_sdk.utils.custom_types.hexbytes import HexBytes
import py_pcapplusplus as pypcap

L4_PROTO_TCP = 0x6
L4_PROTO_UDP = 0x11
TEMP_LISTEN_PORT = 42700


class SOMEIP_EVTGROUP_INFO(BaseModel):
    initial_data: Optional[str] = None


class SOMEIP_METHOD_INFO(BaseModel):
    method_id: int
    payload: HexBytes

class SOMEIP_ENDPOINT_OPTION(BaseModel):
    endpoint_addr: IPvAnyAddress
    port: int
    port_type: pypcap.SomeIpSdProtocolType

    def __str__(self):
        return f"Endpoint address: {self.endpoint_addr}, Port: {self.port}, Transport type: {'UDP' if self.port_type == pypcap.SomeIpSdProtocolType.SD_UDP else 'TCP'}"

class SOMEIP_SERVICE_INFO(BaseModel):
    service_id: int
    instance_id: int
    major_ver: int
    minor_ver: int
    ttl: int
    endpoints: list[SOMEIP_ENDPOINT_OPTION] = []

    def __str__(self):
        return (f"Service ID: {hex(self.service_id)}, "
                f"Instance ID: {hex(self.instance_id)}, "
                f"Version: {self.major_ver}.{self.minor_ver}, "
                f"TTL: {self.ttl}, "
                + ("Endpoints:\n" + f'\n'.join(str(ep) for ep in self.endpoints)) if self.endpoints else ""
                )


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