
from typing import Optional
from enum import Enum, IntFlag
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


class ConfigurationInfoBase(BaseModel):
    def __str__(self):
        return str()

@pydantic_enum_by_name
class EthIfFlags(IntFlag):
    """Enum for Ethernet interface flags
    """
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
    """Enum for the state of the Ethernet interface
    """
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


class IpRoute(BaseModel):
    gateway: Optional[str] = Field(default=None, 
                                   description="Optional parameter the route gateway, none for default gateway")

class CanFdOptions(BaseModel):
    dbitrate: int = Field(default=2000000, description="The data bitrate")

    def __str__(self):
        return f"dbitrate: {self.dbitrate}"

class CanInterfaceConfigurationInfo(ConfigurationInfoBase):
    """Model of the parameters for the CAN interface configurations
    """
    channel: str = Field(description="The CAN interface e.g. can0")
    state: InterfaceState = Field(default=InterfaceState.UP.name, description="The state of the CAN interface - UP/DOWN")
    bitrate: int = Field(default=500000, description="Bitrate")
    sample_point: float = Field(default=0.875, description="Sample-point")
    cc_len8_dlc: bool = Field(description="cc-len8-dlc flag value")
    fd: Optional[CanFdOptions] = Field(default=None, description="Set interface to support CAN-FD")

    def __str__(self):
        return (f"CAN channel: {self.channel}, state {self.state.value}, "
                f"bitrate: {self.bitrate}, sample point: {self.sample_point}, "
                f"len8-dlc: {self.cc_len8_dlc}, "
                f"FD: {str(self.fd) if self.fd else 'Not configured'}"
                )


class IpConfigurationParams(BaseModel):
    """Model of the parameters for the IP configuration
    """
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


DEFAULT_ETH_IF_FLAGS = [EthIfFlags.IFF_BROADCAST.name,
                        EthIfFlags.IFF_MULTICAST.name,
                        EthIfFlags.IFF_UP.name,
                        EthIfFlags.IFF_LOWER_UP.name,
                        EthIfFlags.IFF_RUNNING.name]


class EthInterfaceParams(BaseModel):
    """Model of the parameters for the Ethernet interface configurations
    """
    interface: str = Field(description="The Eth interface to be configured")
    mtu: Optional[int] = Field(default=None, description="MTU (maximum transmission unit)")
    flags: list[EthIfFlags] = Field(default=DEFAULT_ETH_IF_FLAGS, 
                                    description="Flags to apply on the interface")
    state: Optional[InterfaceState] = Field(default=None, description="Interface State to configure")


class EthernetInterfaceConfigurationInfo(ConfigurationInfoBase):
    """Model of the parameters for the Ethernet interface information
    """
    if_params: EthInterfaceParams
    ip_params: list[IpConfigurationParams]

    def __str__(self):
        return (f"Ethernet interface: {self.if_params.interface}\n"
                f"\tMTU: {self.if_params.mtu}, state: {self.if_params.state.value}\n"
                f"\tFlags: " + ", ".join(flag.name for flag in self.if_params.flags) + "\n"
                f"\tIPs: " + ", ".join(ip.cidr_notation for ip in self.ip_params)
                )

class WifiAccessPointConfigurationInfo(ConfigurationInfoBase):
    """Model of the parameters for the Wifi interface information
    """
    ssid: str = Field(description="The SSID of the access point")
    security: str = Field(description="The security access of the access point")
    connected: bool = Field(description="Is the device connected to this access point")

    def __str__(self):
        return f"Wifi Access Point: SSID: {self.ssid}, security: {self.security}, connected: {self.connected}"


class DeviceConfiguration(BaseModel):
    """Model of the parameters for the device configuration information
    """
    configurations_info: list[ConfigurationInfoBase] = []

    def __str__(self):
        return f"\n".join(str(conf_info) for conf_info in self.configurations_info)
