from typing import Any, Type

from faker import Faker
from pydantic import parse_obj_as

faker = Faker()


def compare_as(model: Type, first: Any, second: Any) -> bool:
    return parse_obj_as(model, first) == parse_obj_as(model, second)


__all__ = ["compare_as", "faker"]
