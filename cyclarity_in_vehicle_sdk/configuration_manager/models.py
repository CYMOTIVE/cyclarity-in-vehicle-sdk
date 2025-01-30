
from typing import Optional
from enum import Enum, IntEnum, IntFlag
from pydantic import BaseModel, Field, IPvAnyAddress, model_validator
from ipaddress import IPv4Network, IPv6Network
from pyroute2.netlink.rtnl.ifinfmsg import (
    IFF_UP,
    IFF_BROADCAST,
    IFF_DEBUG,
    IFF_LOOPBACK,
    IFF_POINTOPOINT,
    IFF_NOTRAILERS,
    IFF_RUNNING,
    IFF_NOARP,
    IFF_PROMISC,
    IFF_ALLMULTI,
    IFF_MASTER,
    IFF_SLAVE,
    IFF_MULTICAST,
    IFF_PORTSEL,
    IFF_AUTOMEDIA,
    IFF_DYNAMIC,
    IFF_LOWER_UP,
    IFF_DORMANT,
    IFF_ECHO,
    )
from cyclarity_in_vehicle_sdk.utils.custom_types.enum_by_name import pydantic_enum_by_name

@pydantic_enum_by_name
class EthIfFlags(IntFlag):
    IFF_UP = IFF_UP
    IFF_BROADCAST = IFF_BROADCAST
    IFF_DEBUG = IFF_DEBUG
    IFF_LOOPBACK = IFF_LOOPBACK
    IFF_POINTOPOINT = IFF_POINTOPOINT
    IFF_NOTRAILERS = IFF_NOTRAILERS
    IFF_RUNNING = IFF_RUNNING
    IFF_NOARP = IFF_NOARP
    IFF_PROMISC = IFF_PROMISC
    IFF_ALLMULTI = IFF_ALLMULTI
    IFF_MASTER = IFF_MASTER
    IFF_SLAVE = IFF_SLAVE
    IFF_MULTICAST = IFF_MULTICAST
    IFF_PORTSEL = IFF_PORTSEL
    IFF_AUTOMEDIA = IFF_AUTOMEDIA
    IFF_DYNAMIC = IFF_DYNAMIC
    IFF_LOWER_UP = IFF_LOWER_UP
    IFF_DORMANT = IFF_DORMANT
    IFF_ECHO = IFF_ECHO

    @staticmethod
    def get_flags_from_int(flags: int) -> list:
        ret_flags = []
        for flag in EthIfFlags:
            if flags & flag.value:
                ret_flags.append(flag)

        return ret_flags

class InterfaceState(str, Enum):
    UP = "UP"
    DOWN = "DOWN"
    UNKNOWN = "UNKNOWN"

    @staticmethod
    def state_from_string(str_state: str):
        if str_state.casefold() == InterfaceState.UP.casefold():
            return InterfaceState.UP
        elif str_state.casefold() == InterfaceState.DOWN.casefold():
            return InterfaceState.DOWN
        else:
            return InterfaceState.UNKNOWN

class ConfigurationAction(BaseModel):
    @classmethod
    def get_subclasses(cls):
        return tuple(cls.__subclasses__())

class IpRoute(BaseModel):
    gateway: Optional[str] = None

class IpConfiguration(ConfigurationAction):
    interface: str = Field(description="The network interface for the IP to be configured")
    ip: IPvAnyAddress = Field(description="The IP to configure, IPv4/IPv6")
    suffix: int = Field(description="The subnet notation for this IP address")
    route: Optional[IpRoute] = Field(default=None,
                                     description="Optional parameter for setting a route for the IP")

    @model_validator(mode='after')
    def validate_ip_subnet(self):
        ip_subnet = str(self.ip) + '/' + str(self.suffix)
        if self.ip.version == 6:
            IPv6Network(ip_subnet, False)
        else:
            IPv4Network(ip_subnet, False)
        return self
    
    @property
    def cidr_notation(self) -> str:
        return f"{str(self.ip)}/{str(self.suffix)}"
    
    def __str__(self):
        return f"{self.interface} - {self.cidr_notation}"

class CanConfiguration(ConfigurationAction):
    channel: str
    bitrate: int
    sample_point: float
    cc_len8_dlc: bool

class EthInterfaceConfiguration(ConfigurationAction):
    interface: str = Field(description="The Eth interface to be configured")
    mtu: Optional[int] = Field(default=None, description="MTU (maximum transmission unit)")
    flags: list[EthIfFlags] = Field(default=[], description="Flags to apply on the interface")
    state: Optional[InterfaceState] = Field(default=None, description="Interface State to configure")

class EthernetInterfaceParams(BaseModel):
    if_params: EthInterfaceConfiguration
    ip_params: list[IpConfiguration]

class DeviceConfiguration(BaseModel):
    eth_interfaces: list[EthernetInterfaceParams] = []
    can_interfaces: list[CanConfiguration] = []
