import logging
from typing import NamedTuple
from cyclarity_in_vehicle_sdk.plugin.base.plugin_base import PluginBase, BackgroundPluginBase
from cyclarity_sdk.expert_builder.runnable.runnable import BaseRequiredPluginModel

class PluginEntry(NamedTuple):
    instance: type[PluginBase]
    background: bool

class PluginManager():
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.plugins: dict[str, PluginEntry] = {}

    def add_plugin(self, plugin_instance: type[PluginBase], background: bool = False):
        self.plugins.update({plugin_instance.__class__.__name__: PluginEntry(instance=plugin_instance,
                                                                             background=background)})

    def get_plugin_model(self, plugin_model_type: type[BaseRequiredPluginModel]) -> type[BaseRequiredPluginModel]:
        # Create an instance of the provided class  
        instance = plugin_model_type()  
    
        # Iterate over the class annotations to get the attributes and their types  
        for attribute, attribute_type in plugin_model_type.__annotations__.items():
            # Get an existing plugin that is a subclass of the desired plugin
            plugin = next((plugin_entry.instance for plugin_entry in self.plugins.values() if issubclass(type(plugin_entry.instance), attribute_type)), None) 
            if plugin:
                setattr(instance, attribute, plugin)
            else:
                raise RuntimeError(f"Required plugin is not available {attribute_type.__name__}")
    
        return instance
    
    def start_background_plugins(self):
        for plugin_name, plugin_entry in self.plugins.items():
            if plugin_entry.background:
                assert issubclass(plugin_entry.instance, BackgroundPluginBase)
                self.logger.debug(f"Starting background plugin {plugin_name}")
                plugin_entry.start()


    async def stop_background_plugins(self):
        for plugin_name, plugin_entry in self.plugins.items():
            if plugin_entry.background:
                assert issubclass(plugin_entry.instance, BackgroundPluginBase)
                self.logger.debug(f"Stopping background plugin {plugin_name}")
                await plugin_entry.stop()
                self.plugins[plugin_name].background = False