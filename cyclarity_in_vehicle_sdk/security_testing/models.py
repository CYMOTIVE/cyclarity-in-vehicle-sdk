import inspect
from typing import NamedTuple, Optional, Type, Union
from pydantic import BaseModel
from abc import abstractmethod


class StepResult(BaseModel):
    success: bool
    fail_reason: Optional[str] = None
    def __bool__(self) -> bool:
        return self.success
    def __str__(self) -> str:
        if self.success:
            return "Success"
        return f"Failed: {self.fail_reason}"


class BaseTestOutput(BaseModel):
    @classmethod  
    def get_non_abstract_subclasses(cls) -> list[Type]:
        subclasses = []

        for subclass in cls.__subclasses__():
            # If subclass has no subclasses and is non-abstract, it's a leaf
            if not subclass.__subclasses__() and not inspect.isabstract(subclass):
                subclasses.append(subclass)
            else:
                # Otherwise check its subclasses
                subclasses.extend(subclass.get_non_abstract_subclasses())

        return subclasses

    @abstractmethod
    def validate(self, step_output: "BaseTestOutput", prev_outputs: list["BaseTestOutput"] = []) -> StepResult:
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
