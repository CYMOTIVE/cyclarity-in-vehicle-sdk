from abc import abstractmethod
from cyclarity_in_vehicle_sdk.plugin.plugin_base import PluginBase


class ResetPluginBase(PluginBase):
    @abstractmethod
    def reset(self):
        pass