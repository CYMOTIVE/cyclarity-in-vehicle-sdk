import time
import gpiod
from pydantic import Field
from cyclarity_in_vehicle_sdk.plugin.base.reset_plugin_base import ResetPluginBase

class RelayResetPlugin(ResetPluginBase):
    reset_pin: int = Field(ge=0, description="Reset relay gpio pin")
    gpio_chip: str = Field(description="The gpio chip connected to the relay e.g. /dev/gpiochip4")

    def setup(self) -> None:
        self.relay = gpiod.request_lines(self.gpio_chip, consumer="relay", config={
            self.reset_pin: gpiod.LineSettings(
                direction=gpiod.line.Direction.OUTPUT,
                output_value=gpiod.line.Value.INACTIVE
            )
        })        

    def teardown(self) -> None:
        if hasattr(self, "relay"):
            self.relay.release()

    def reset(self) -> bool:
        if hasattr(self, "relay"):
            self.logger.debug("Trying to reset the ECU")
            self.relay.set_value(self.reset_pin, gpiod.line.Value.ACTIVE)
            time.sleep(1)
            self.relay.set_value(self.reset_pin, gpiod.line.Value.INACTIVE)
            time.sleep(1)
            return True
        else: 
            self.logger.error("relay is not available, either setup() was no performed or it has failed")
            return False