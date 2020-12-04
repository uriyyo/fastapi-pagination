from typing import Any, List, Type, TypeVar

from faker import Faker
from pydantic import parse_obj_as

faker = Faker()

T = TypeVar("T")


def normalize(model: Type[T], *models: Any) -> List[T]:
    return [parse_obj_as(model, m) for m in models]


__all__ = ["normalize", "faker"]
