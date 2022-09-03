from typing import Any, List, Type, TypeVar

from faker import Faker
from pydantic import BaseModel

faker = Faker()

T = TypeVar("T", bound=BaseModel)


def normalize(model: Type[T], *models: Any) -> List[T]:
    return [model.parse_obj(m) for m in models]


__all__ = [
    "normalize",
    "faker",
]
