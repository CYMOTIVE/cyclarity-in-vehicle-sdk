
from typing import Literal
from cyclarity_in_vehicle_sdk.configuration_manager.models import CanInterfaceConfigurationInfo, EthInterfaceParams, IpConfigurationParams
from pydantic import BaseModel, Field


class ConfigurationAction(BaseModel):
    @classmethod
    def get_subclasses(cls):
        return tuple(cls.__subclasses__())


class IpAddAction(ConfigurationAction, IpConfigurationParams):
    action_type: Literal['add'] = 'add'


class IpRemoveAction(ConfigurationAction, IpConfigurationParams):
    action_type: Literal['del'] = 'del'


class WifiConnectAction(ConfigurationAction):
    ssid: str = Field(description="The SSID of the access point to connect to")
    password: str = Field(description="The pass phrase to use for connecting")


class CanConfigurationAction(ConfigurationAction, CanInterfaceConfigurationInfo):
    pass


class EthInterfaceConfigurationAction(ConfigurationAction, EthInterfaceParams):
    pass

