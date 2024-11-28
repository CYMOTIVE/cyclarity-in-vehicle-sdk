from abc import abstractmethod
from cyclarity_in_vehicle_sdk.plugin.base.plugin_base import BackgroundPluginBase, EventNotifierPluginBase, InteractivePluginBase


class BackgroundCrashDetectionPluginBase(EventNotifierPluginBase, BackgroundPluginBase):
    """ Base class for crash detection plugins
    """
    pass

class InteractiveCrashDetectionPluginBase(InteractivePluginBase):
    """ Base class for crash detection plugins
    """
    @abstractmethod
    def check_crash(self) -> bool:
        pass