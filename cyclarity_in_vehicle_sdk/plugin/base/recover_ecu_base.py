from abc import abstractmethod
from cyclarity_in_vehicle_sdk.plugin.base.plugin_base import InteractivePluginBase


class RecoverEcuPluginBase(InteractivePluginBase):
    """ Base class for plugins responsible of recovering the ECU back to predefined state
    """
    @abstractmethod
    def recover(self) -> bool:
        """Recover the ECU to a predefined state
        Returns:
            bool: True if recovery operation succeeded, False otherwise.
        """
        pass