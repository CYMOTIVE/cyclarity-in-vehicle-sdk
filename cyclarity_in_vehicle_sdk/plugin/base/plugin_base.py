from abc import abstractmethod
import threading
from typing import Callable
from cyclarity_sdk.expert_builder.runnable.runnable import ParsableModel
from pydantic import PrivateAttr

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


class BackgroundPluginBase(PluginBase):
    """Base for plugins that shall run in the background
    """
    _thread: threading.Thread = None
    _stop_event: threading.Event = PrivateAttr(default_factory=threading.Event)    

    @abstractmethod  
    def run(self) -> None:
        """To be implemented by concrete background plugins
        `_stop_event` must be used to identify and respond to `stop` requests
        e.g.
        ```
        def run(self) -> None:
            while not self._stop_event.is_set():
                do_stuff..
        ```
        """
        pass

    def start(self):  
        """Will run the derived run() operation in an async manner
        """
        if self._thread is None: 
            self._thread = threading.Thread(target=self.run)
            self._thread.start()
  
    def stop(self):  
        """Will stop the async operation started in start() if still needed
        """ 
        if self._thread is not None:
            self._stop_event.set()  
            self._thread.join()
            self._thread = None

class EventNotifierPluginBase(PluginBase):
    """Base for plugins that shall notify the user upon occurring events
    """
    _event_notifier_cb: Callable[[], None] = None

    def set_notifier(self, on_event_callback: Callable[[], None], on_error_callback: Callable[[], None]):
        """Sets a callback to be used for notification upon occurring events
        Args:
            on_event_callback (Callable[[], None]): the callback to be called upon events
            on_error_callback (Callable[[], None]): the callback to be called upon errors
        """
        self._event_notifier_cb = on_event_callback
        self._error_notifier_cb = on_error_callback


class InteractivePluginBase(PluginBase):
    """Base for plugins that require interaction (API calls) by the using entity
    """
    pass