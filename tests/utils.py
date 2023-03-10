from typing import Any, List, Type, TypeVar

from faker import Faker
from pydantic import BaseModel

from fastapi_pagination import Page, LimitOffsetPage
from fastapi_pagination.default import OptionalParams
from fastapi_pagination.limit_offset import OptionalLimitOffsetParams

faker = Faker()

T = TypeVar("T", bound=BaseModel)


def normalize(model: Type[T], *models: Any) -> List[T]:
    return [model.parse_obj(m) for m in models]


OptionalPage = Page.with_params(OptionalParams)
OptionalLimitOffsetPage = LimitOffsetPage.with_params(OptionalLimitOffsetParams)


__all__ = [
    "normalize",
    "faker",
    "OptionalPage",
    "OptionalLimitOffsetPage",
]
