from enum import Enum, auto
from cyclarity_in_vehicle_sdk.utils.custom_types.enum_by_name import pydantic_enum_by_name
from cryptography.hazmat.primitives.hashes import (
    SHA1,
    SHA512_224,
    SHA512_256,
    SHA224,
    SHA256,
    SHA384,
    SHA512,
    SHA3_224,
    SHA3_256,
    SHA3_384,
    SHA3_512,
    MD5,
    SM3,
    )


@pydantic_enum_by_name
class AsymmetricPaddingType(Enum):
    PKCS1v15 = auto()
    PSS = auto()
    OAEP = auto()


@pydantic_enum_by_name
class HashingAlgorithm(Enum):
    SHA1 = auto()
    SHA512_224 = auto()
    SHA512_256 = auto()
    SHA224 = auto()
    SHA256 = auto()
    SHA384 = auto()
    SHA512 = auto()
    SHA3_224 = auto()
    SHA3_256 = auto()
    SHA3_384 = auto()
    SHA3_512 = auto()
    MD5 = auto()
    SM3 = auto()

    @staticmethod
    def enum_to_method(val):
        match val:
            case HashingAlgorithm.SHA1:
                return SHA1()
            case HashingAlgorithm.SHA512_224:
                return SHA512_224()
            case HashingAlgorithm.SHA512_256:
                return SHA512_256()
            case HashingAlgorithm.SHA224:
                return SHA224()
            case HashingAlgorithm.SHA256:
                return SHA256()
            case HashingAlgorithm.SHA384:
                return SHA384()
            case HashingAlgorithm.SHA512:
                return SHA512()
            case HashingAlgorithm.SHA3_224:
                return SHA3_224()
            case HashingAlgorithm.SHA3_256:
                return SHA3_256()
            case HashingAlgorithm.SHA3_384:
                return SHA3_384()
            case HashingAlgorithm.SHA3_512:
                return SHA3_512()
            case HashingAlgorithm.MD5:
                return MD5()
            case HashingAlgorithm.SM3:
                return SM3()
            case _:
                raise ValueError(f"invalid argument: {val}")
