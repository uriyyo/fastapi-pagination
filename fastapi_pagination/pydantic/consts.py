from pydantic import VERSION

IS_PYDANTIC_V2 = VERSION.startswith("2.")

__all__ = [
    "IS_PYDANTIC_V2",
]
