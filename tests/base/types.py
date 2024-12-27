__all__ = [
    "MakeOptionalPage",
    "PaginationCaseType",
    "PaginationType",
]

from functools import cache
from typing import TYPE_CHECKING, Annotated, Any, TypeVar

from typing_extensions import Literal, TypeAlias

from fastapi_pagination.bases import AbstractPage
from fastapi_pagination.customization import CustomizedPage, UseOptionalParams

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
else:

    class MakeOptionalPage:
        @classmethod
        @cache
        def __class_getitem__(cls, item):
            return CustomizedPage[item, UseOptionalParams()]
