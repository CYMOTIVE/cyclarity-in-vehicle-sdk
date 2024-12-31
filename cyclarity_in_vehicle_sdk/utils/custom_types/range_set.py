"""
NmapRanges type class 
"""

from typing import (
    Any,
    Type,
    Union,
)

from jsonargparse.typing import register_type
from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema

class BaseNumberRangeSet():
    """Base class for parsing and representing a set of numeric ranges."""

    def __init__(self, input_string: str = ""):
        self._input_string = input_string
        self.ranges = self._parse_nmap_ranges(input_string)

    def __iter__(self):
        for r in self.ranges:
            for i in r:
                yield i

    def __repr__(self):
        return self._input_string

    def __len__(self):
        return sum(len(r) for r in self.ranges)

    def __eq__(self, _value: "BaseNumberRangeSet") -> bool:
        try:
            return _value.ranges == self.ranges
        except (TypeError, AttributeError):
            return False

    @classmethod
    def _parse_nmap_ranges(cls, nmap_ranges: str) -> list[range]:
        if not nmap_ranges:
            return []
        tokens = nmap_ranges.split(",")
        ranges = []
        for t in tokens:
            if "-" in t:
                start, stop = (cls._parse_number(x) for x in t.split("-"))
            else:
                start = stop = cls._parse_number(t)

            ranges.append(range(start, stop + 1))
        return sorted(ranges, key=lambda x: x.stop)
    
    @staticmethod
    def _parse_number(number_string: str) -> int:
        raise NotImplementedError

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source: Type[Any], handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_after_validator_function(
            cls._validate,
            cls._schema(),
            serialization=core_schema.plain_serializer_function_ser_schema(
                cls._serialize,
                info_arg=False,
                return_schema=cls._schema(),
            ),
        )

    @staticmethod
    def _serialize(value: "BaseNumberRangeSet") -> str:
        return value._input_string

    @classmethod
    def _validate(cls, value: Union[str, "BaseNumberRangeSet"]) -> "BaseNumberRangeSet":
        if isinstance(value, BaseNumberRangeSet):
            return value
        else:
            return cls(value)

    @classmethod
    def _schema(cls) -> str:
        return core_schema.union_schema(
            [core_schema.str_schema(), core_schema.is_instance_schema(cls=cls)]
        )

class HexNumberRangeSet(BaseNumberRangeSet): 
    """Subclass for parsing and representing a set of hexadecimal numeric ranges.""" 
    @staticmethod
    def _parse_number(number_string):  
        return int(number_string, 16)  
  
class OctNumberRangeSet(BaseNumberRangeSet):  
    """Subclass for parsing and representing a set of octal numeric ranges."""
    @staticmethod
    def _parse_number(number_string):  
        return int(number_string, 8)  
  
class BinNumberRangeSet(BaseNumberRangeSet):  
    """Subclass for parsing and representing a set of binary numeric ranges."""
    @staticmethod
    def _parse_number(number_string):  
        return int(number_string, 2)  
  
class DecNumberRangeSet(BaseNumberRangeSet):  
    """Subclass for parsing and representing a set of decimal numeric ranges."""
    @staticmethod
    def _parse_number(number_string):  
        return int(number_string, 10)  

class AutoNumberRangeSet(BaseNumberRangeSet):  
    """Subclass for parsing and representing a set of decimal numeric ranges. 
    with an option to modify the parsing type using prefixes.
    hex: 0x100-0X200
    bin: 0b100-0B110
    oct: 0o100-0O200
    """
    @staticmethod
    def _parse_number(number_string):  
        return int(number_string, 0)  

register_type(type_class=HexNumberRangeSet, serializer=str, deserializer=HexNumberRangeSet)
register_type(type_class=DecNumberRangeSet, serializer=str, deserializer=DecNumberRangeSet)
register_type(type_class=OctNumberRangeSet, serializer=str, deserializer=OctNumberRangeSet)
register_type(type_class=BinNumberRangeSet, serializer=str, deserializer=BinNumberRangeSet)
register_type(type_class=AutoNumberRangeSet, serializer=str, deserializer=AutoNumberRangeSet)