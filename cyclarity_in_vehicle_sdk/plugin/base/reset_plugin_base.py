from abc import abstractmethod
from cyclarity_in_vehicle_sdk.plugin.base.plugin_base import InteractivePluginBase


class ResetPluginBase(InteractivePluginBase):
    """ Base class for reset plugins
    """
    @abstractmethod
    def reset(self) -> bool:
        """Resets the target device
        Returns:
            bool: True if reset operation succeeded, False otherwise.
        """
        pass