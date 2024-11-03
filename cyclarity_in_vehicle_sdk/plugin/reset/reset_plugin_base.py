from abc import abstractmethod
from cyclarity_in_vehicle_sdk.plugin.plugin_base import InteractivePluginBase


class ResetPluginBase(InteractivePluginBase):
    @abstractmethod
    def reset(self):
        pass