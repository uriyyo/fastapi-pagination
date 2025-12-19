from pydantic import VERSION

IS_PYDANTIC_V2 = VERSION.startswith("2.")
IS_PYDANTIC_V2_12_OR_HIGHER = IS_PYDANTIC_V2 and tuple(int(part) for part in VERSION.split(".")[:2]) >= (2, 12)

__all__ = [
    "IS_PYDANTIC_V2",
    "IS_PYDANTIC_V2_12_OR_HIGHER",
]
