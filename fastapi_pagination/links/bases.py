__all__ = [
    "BaseUseLinks",
    "Links",
    "create_links",
]

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Generic, Optional

from pydantic import BaseModel, Field
from starlette.requests import URL
from typing_extensions import TypeVar

from fastapi_pagination.api import request
from fastapi_pagination.bases import AbstractPage
from fastapi_pagination.customization import ClsNamespace, PageCls, PageCustomizer
from fastapi_pagination.errors import UnsupportedFeatureError
from fastapi_pagination.utils import IS_PYDANTIC_V2

_link_field = (
    Field(examples=["/api/v1/users?limit=1&offset1"])
    if IS_PYDANTIC_V2
    else Field(example="/api/v1/users?limit=1&offset1")  # type: ignore[call-overload]
)


class Links(BaseModel):
    first: Optional[str] = _link_field
    last: Optional[str] = _link_field
    self: Optional[str] = _link_field
    next: Optional[str] = _link_field
    prev: Optional[str] = _link_field


def _only_path(url: URL) -> str:
    if not url.query:
        return str(url.path)

    return f"{url.path}?{url.query}"


def _update_path(url: URL, to_update: Optional[Mapping[str, Any]]) -> Optional[str]:
    if to_update is None:
        return None

    return _only_path(url.include_query_params(**to_update))


def create_links(
    first: Mapping[str, Any],
    last: Mapping[str, Any],
    next: Optional[Mapping[str, Any]],  # noqa: A002
    prev: Optional[Mapping[str, Any]],
) -> Links:
    req = request()
    url = req.url

    return Links(
        self=_only_path(url),
        first=_update_path(url, first),
        last=_update_path(url, last),
        next=_update_path(url, next),
        prev=_update_path(url, prev),
    )


TPage_contra = TypeVar("TPage_contra", bound=AbstractPage, contravariant=True, default=Any)


@dataclass
class BaseUseLinks(PageCustomizer, Generic[TPage_contra], ABC):
    field: str = "links"

    @abstractmethod
    def resolve_links(self, _page: TPage_contra, /) -> Links:
        pass

    def customize_page_ns(self, page_cls: PageCls, ns: ClsNamespace) -> None:
        if not IS_PYDANTIC_V2:
            raise UnsupportedFeatureError("UseLinks customization is not supported for Pydantic v1")

        from pydantic import computed_field

        ns[self.field] = computed_field(return_type=Links)(lambda _self: self.resolve_links(_self))
