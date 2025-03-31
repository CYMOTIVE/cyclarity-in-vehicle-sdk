
from typing import Literal
from cyclarity_in_vehicle_sdk.configuration_manager.models import CanInterfaceConfigurationInfo, EthInterfaceParams, IpConfigurationParams
from pydantic import BaseModel, Field


class ConfigurationAction(BaseModel):
    @classmethod
    def get_subclasses(cls):
        return tuple(cls.__subclasses__())


class IpAddAction(ConfigurationAction, IpConfigurationParams):
    """Action for adding an IP address to an ethernet interface
    """
    action_type: Literal['add_ip'] = 'add_ip'


class IpRemoveAction(ConfigurationAction, IpConfigurationParams):
    """Action for removing an IP address to an ethernet interface
    """
    action_type: Literal['del_ip'] = 'del_ip'


class WifiConnectAction(ConfigurationAction):
    """Action for connecting to a wifi network
    """
    action_type: Literal['wifi_connect'] = 'wifi_connect'
    ssid: str = Field(description="The SSID of the access point to connect to")
    password: str = Field(description="The pass phrase to use for connecting")


class CanConfigurationAction(ConfigurationAction, CanInterfaceConfigurationInfo):
    """Action for configuring the CAN interface
    """
    action_type: Literal['con_conf'] = 'con_conf'


class EthInterfaceConfigurationAction(ConfigurationAction, EthInterfaceParams):
    """Action for configuring the Ethernet interface
    """
    action_type: Literal['eth_conf'] = 'eth_conf'


class CreateVlanAction(ConfigurationAction):
    """Action for creating a VLAN interface linked to an actual Eth interface
    """
    action_type: Literal['vlan_create'] = 'vlan_create'
    if_name: str = Field(description="The new vlan interface name")
    if_link: str = Field(description="The physical interface to link to")
    vlan_id: int = Field(description="The vlan ID")