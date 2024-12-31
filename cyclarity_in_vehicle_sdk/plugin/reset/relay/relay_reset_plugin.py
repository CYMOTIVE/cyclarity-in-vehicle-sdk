from enum import Enum
import time
from typing import Union
import gpiod
from pydantic import Field
from cyclarity_in_vehicle_sdk.plugin.base.reset_plugin_base import ResetPluginBase
from cyclarity_in_vehicle_sdk.utils.custom_types.enum_by_name import pydantic_enum_by_name

@pydantic_enum_by_name
class GpioChip(str, Enum):
    PI4 = "/dev/gpiochip0"
    PI5 = "/dev/gpiochip4"

class RelayResetPlugin(ResetPluginBase):
    reset_pin: int = Field(ge=0, description="Reset relay gpio pin")
    gpio_chip: Union[GpioChip, str] = Field(description="The gpio chip connected to the relay e.g. /dev/gpiochip4")
    shutdown_sleep: float = Field(default=1, gt=0, description="Sleep after shutdown request, default to 1 second")
    boot_sleep: float = Field(default=1, gt=0, description="Sleep after boot request, default to 1 second")
    _relay: gpiod.LineRequest = None

    def setup(self) -> None:
        try:
            self._relay = gpiod.request_lines(self.gpio_chip, consumer="relay", config={
                self.reset_pin: gpiod.LineSettings(
                    direction=gpiod.line.Direction.OUTPUT,
                    output_value=gpiod.line.Value.INACTIVE
                )
            })
        except Exception as ex:
            self.logger.error(f"Failed setting up RelayResetPlugin, error: {ex}")

    def teardown(self) -> None:
        if self._relay:
            self._relay.release()

    def reset(self) -> bool:
        if self._relay:
            self.logger.debug("Trying to reset the ECU")
            self._relay.set_value(self.reset_pin, gpiod.line.Value.ACTIVE)
            time.sleep(self.shutdown_sleep)
            self._relay.set_value(self.reset_pin, gpiod.line.Value.INACTIVE)
            time.sleep(self.boot_sleep)
            return True
        else: 
            self.logger.error("relay is not available, either setup() was no performed or it has failed")
            return False