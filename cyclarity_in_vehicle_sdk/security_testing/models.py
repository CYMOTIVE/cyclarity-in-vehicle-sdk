import inspect
from typing import NamedTuple, Type, Union
from pydantic import BaseModel
from abc import abstractmethod


class BaseTestOutput(BaseModel):
    @classmethod  
    def get_non_abstract_subclasses(cls) -> list[Type]:  
        subclasses = []  
  
        for subclass in cls.__subclasses__():  
            # Check if the subclass itself has any subclasses  
            subclasses.extend(subclass.get_non_abstract_subclasses())  
              
            # Check if the subclass is non-abstract  
            if not inspect.isabstract(subclass):  
                subclasses.append(subclass)  
  
        return subclasses  
    
    @abstractmethod
    def is_success(self, step_output: "BaseTestOutput", prev_outputs: list["BaseTestOutput"] = []) -> bool:
        raise NotImplementedError


class BaseTestAction(BaseModel):
    @classmethod  
    def get_non_abstract_subclasses(cls) -> list[Type]:  
        subclasses = []  
  
        for subclass in cls.__subclasses__():  
            # Check if the subclass itself has any subclasses  
            subclasses.extend(subclass.get_non_abstract_subclasses())  
              
            # Check if the subclass is non-abstract  
            if not inspect.isabstract(subclass):  
                subclasses.append(subclass)  
  
        return subclasses  
    
    @abstractmethod
    def execute() -> BaseTestOutput:
        raise NotImplementedError
