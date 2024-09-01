from abc import ABCMeta, abstractmethod
from cyclarity_sdk.expert_builder.runnable.runnable import ParsableModel
from typing import Tuple, Optional


class IDeviceShell (ParsableModel, metaclass=ABCMeta):
    @abstractmethod
    def exec_command (self, command: str, testcase_filter: Optional[str] = None) -> Tuple[str, ...]:
        """
    This is an abstract method that should be implemented in subclasses.
    It is intended to execute a given command and optionally filter the results.

    :param command: String that represents the command to be executed.
    :param testcase_filter: Optional string that, if provided, will be used to filter the command's output.
                            Only the lines containing this string will be included in the result.
    :return: A tuple containing the lines of the command's output that match the testcase_filter.
             If no filter is provided, it returns all output lines.
    """

    @abstractmethod
    def teardown (self):
        """
        This is an abstract method that should be implemented in subclasses.
        It is intended to perform cleanup operations (like closing connections).
         """
