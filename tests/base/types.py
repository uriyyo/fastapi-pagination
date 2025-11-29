__all__ = [
    "MakeOptionalPage",
    "MakePydanticV1Page",
    "PaginationCaseType",
    "PaginationType",
]

from functools import cache
from typing import TYPE_CHECKING, Annotated, Any, Literal, TypeAlias, TypeVar

from fastapi_pagination.bases import AbstractPage
from fastapi_pagination.customization import CustomizedPage, UseOptionalParams, UsePydanticV1

PaginationType: TypeAlias = Literal[
    "page-size",
    "limit-offset",
    "cursor",
]
PaginationCaseType: TypeAlias = Literal[
    "default",
    "non-scalar",
    "relationship",
    "optional",
]

if TYPE_CHECKING:
    TPage = TypeVar("TPage", bound=AbstractPage[Any])

    MakeOptionalPage = Annotated[
        TPage,
        ...,
    ]

    MakePydanticV1Page = Annotated[
        TPage,
        ...,
    ]
else:

    class MakeOptionalPage:
        @classmethod
        @cache
        def __class_getitem__(cls, item):
            return CustomizedPage[item, UseOptionalParams()]

    class MakePydanticV1Page:
        @classmethod
        @cache
        def __class_getitem__(cls, item):
            return CustomizedPage[item, UsePydanticV1()]
