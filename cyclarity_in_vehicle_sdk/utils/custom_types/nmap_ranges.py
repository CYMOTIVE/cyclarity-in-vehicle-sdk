from jsonargparse.typing import register_type
from .range_set import HexNumberRangeSet

# This type is deprecated and renamed to HexNumberRangeSet

NmapRanges = HexNumberRangeSet
register_type(type_class=NmapRanges, serializer=str, deserializer=NmapRanges)
