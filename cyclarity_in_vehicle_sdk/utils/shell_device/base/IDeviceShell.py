from abc import ABCMeta, abstractmethod
from cyclarity_sdk.expert_builder.runnable.runnable import ParsableModel
from typing import Tuple, Optional, Union


class IDeviceShell (ParsableModel, metaclass=ABCMeta):
    @abstractmethod
    def exec_command(self, command: str, testcase_filter: Optional[str] = None, return_stderr: bool = False, verbose: bool=False) -> Union[Tuple[str, ...], Tuple[Tuple[str, ...], str]]:  
        """  
        This method executes a given command via ssh and returns the output.  
        If a testcase_filter is provided, it only returns lines that contain the filter string.  
        If return_stderr is True, it also returns the stderr content.  
    
        :param command: String that represents the command to be executed.  
        :param testcase_filter: Optional string used to filter the command's output.  
        :param return_stderr: Optional boolean used to determine if stderr should be returned.  
        :param verbose: Optional boolean used to log execution data
        :return: A tuple containing the command's output lines that match the testcase_filter and optionally stderr content.  
                If no filter is provided, it returns all output lines.  
        """  
    
    @abstractmethod
    def teardown (self):
        """
        This is an abstract method that should be implemented in subclasses.
        It is intended to perform cleanup operations (like closing connections).
         """
