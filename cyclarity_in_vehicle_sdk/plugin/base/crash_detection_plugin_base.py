from abc import abstractmethod
from cyclarity_in_vehicle_sdk.plugin.base.plugin_base import BackgroundPluginBase, EventNotifierPluginBase


class CrashDetectionPluginBase(EventNotifierPluginBase, BackgroundPluginBase):
    """ Base class for crash detection plugins
    """
    pass