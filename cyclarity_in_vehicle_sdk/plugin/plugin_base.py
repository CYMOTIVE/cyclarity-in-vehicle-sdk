from abc import abstractmethod
import asyncio
from cyclarity_sdk.expert_builder.runnable.runnable import ParsableModel


class PluginBase(ParsableModel):
    @abstractmethod
    def setup(self) -> None:
        """Setup the plugin
        """
        pass

    @abstractmethod
    def teardown(self) -> None:
        """Teardown the plugin
        """
        pass


class NonInteractivePluginBase(PluginBase):
    _task: asyncio.Task = None

    @abstractmethod  
    async def run(self) -> None:
        """To be implemented by concrete Non interactive plugins
        """
        pass

    async def _run_wrapper(self):
        try:  
            await self.run()  
        except asyncio.CancelledError:  
            pass
  
    def start(self):  
        """Will run the derived run() operation in an async manner
        """
        if self._task is None:  
            self._task = asyncio.create_task(self._run_wrapper())
  
    async def stop(self):  
        """Will stop the async operation started in start() if still needed
        """  
        if self._task is not None:  
            self._task.cancel()  
            await self._task
            self._task = None  