
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
    action_type: Literal['add'] = 'add'


class IpRemoveAction(ConfigurationAction, IpConfigurationParams):
    """Action for removing an IP address to an ethernet interface
    """
    action_type: Literal['del'] = 'del'


class WifiConnectAction(ConfigurationAction):
    """Action for connecting to a wifi network
    """
    ssid: str = Field(description="The SSID of the access point to connect to")
    password: str = Field(description="The pass phrase to use for connecting")


class CanConfigurationAction(ConfigurationAction, CanInterfaceConfigurationInfo):
    """Action for configuring the CAN interface
    """
    pass


class EthInterfaceConfigurationAction(ConfigurationAction, EthInterfaceParams):
    """Action for configuring the Ethernet interface
    """
    pass

