from typing import Annotated, Any
from pydantic import (
    PlainSerializer,
    PlainValidator,
    errors,
    WithJsonSchema,
)

def hex_bytes_validator(val: Any) -> bytes:
    if isinstance(val, bytes):
        return val
    elif isinstance(val, bytearray):
        return bytes(val)
    elif isinstance(val, str):
        return bytes.fromhex(val)
    raise errors.BytesError()

HexBytes = Annotated[bytes, PlainValidator(hex_bytes_validator), PlainSerializer(lambda v: v.hex()), WithJsonSchema({'type': 'string'})]