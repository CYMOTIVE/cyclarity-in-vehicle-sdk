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

class NmapRanges():
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

    def __eq__(self, _value: "NmapRanges") -> bool:
        try:
            return _value.ranges == self.ranges
        except (TypeError, AttributeError):
            return False

    @staticmethod
    def _parse_nmap_ranges(nmap_ranges: str) -> list[range]:
        if not nmap_ranges:
            return []
        tokens = nmap_ranges.split(",")
        ranges = []
        for t in tokens:
            if "-" in t:
                start, stop = (int(x, 16) for x in t.split("-"))
            else:
                start = stop = int(t, 16)

            ranges.append(range(start, stop + 1))
        return sorted(ranges, key=lambda x: x.stop)

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
    def _serialize(value: "NmapRanges") -> str:
        return value._input_string

    @staticmethod
    def _validate(value: Union[str, "NmapRanges"]) -> "NmapRanges":
        if type(value) is NmapRanges:
            return value
        else:
            return NmapRanges(value)

    @staticmethod
    def _schema() -> str:
        return core_schema.union_schema(
            [core_schema.str_schema(), core_schema.is_instance_schema(cls=NmapRanges)]
        )


register_type(type_class=NmapRanges, serializer=str, deserializer=NmapRanges)