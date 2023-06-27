from typing import Any, List, Type, TypeVar

from faker import Faker
from pydantic import BaseModel

from fastapi_pagination import LimitOffsetPage, Page
from fastapi_pagination.default import OptionalParams
from fastapi_pagination.limit_offset import OptionalLimitOffsetParams
from fastapi_pagination.utils import IS_PYDANTIC_V2

faker = Faker()

T = TypeVar("T", bound=BaseModel)

if IS_PYDANTIC_V2:

    def parse_obj(model: Type[T], obj: Any) -> T:
        return model.model_validate(obj, from_attributes=True)

else:

    def parse_obj(model: Type[T], obj: Any) -> T:
        return model.parse_obj(obj)


def normalize(model: Type[T], *models: Any) -> List[T]:
    return [parse_obj(model, m) for m in models]


OptionalPage = Page.with_params(OptionalParams)
OptionalLimitOffsetPage = LimitOffsetPage.with_params(OptionalLimitOffsetParams)


__all__ = [
    "normalize",
    "faker",
    "OptionalPage",
    "OptionalLimitOffsetPage",
]
