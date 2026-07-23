__all__ = [
    "BaseLinksCustomizer",
    "BaseUseHeaderLinks",
    "BaseUseLinks",
    "Links",
    "create_links",
]

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Generic

from pydantic import BaseModel, Field, computed_field
from starlette.requests import URL
from typing_extensions import TypeVar

from fastapi_pagination.api import request, response
from fastapi_pagination.bases import AbstractPage
from fastapi_pagination.customization import ClsNamespace, PageCls, PageCustomizer

_link_field = Field(default=None, examples=["/api/v1/users?limit=1&offset1"])


class Links(BaseModel):
    first: str | None = _link_field
    last: str | None = _link_field
    self: str | None = _link_field
    next: str | None = _link_field
    prev: str | None = _link_field


def _resolve_path(
    url: URL,
    *,
    only_path: bool | None = None,
) -> str:
    if only_path is None:
        only_path = True

    if not only_path:
        return str(url)

    if not url.query:
        return str(url.path)

    return f"{url.path}?{url.query}"


def _update_path(
    url: URL,
    to_update: Mapping[str, Any] | None,
    *,
    only_path: bool | None = None,
) -> str | None:
    if to_update is None:
        return None

    return _resolve_path(url.include_query_params(**to_update), only_path=only_path)


def create_links(
    first: Mapping[str, Any],
    last: Mapping[str, Any],
    next: Mapping[str, Any] | None,  # noqa: A002
    prev: Mapping[str, Any] | None,
    *,
    only_path: bool | None = None,
) -> Links:
    req = request()
    url = req.url

    return Links(
        self=_resolve_path(url, only_path=only_path),
        first=_update_path(url, first, only_path=only_path),
        last=_update_path(url, last, only_path=only_path),
        next=_update_path(url, next, only_path=only_path),
        prev=_update_path(url, prev, only_path=only_path),
    )


TPage_contra = TypeVar("TPage_contra", bound=AbstractPage, contravariant=True, default=Any)


@dataclass
class BaseLinksCustomizer(PageCustomizer, ABC, Generic[TPage_contra]):
    only_path: bool = True

    @abstractmethod
    def resolve_links(self, _page: TPage_contra, /) -> Links:
        pass


@dataclass
class BaseUseLinks(BaseLinksCustomizer[TPage_contra], ABC):
    field: str = "links"

    def customize_page_ns(self, page_cls: PageCls, ns: ClsNamespace) -> None:
        ns[self.field] = computed_field(return_type=Links)(lambda _self: self.resolve_links(_self))


@dataclass
class BaseUseHeaderLinks(BaseLinksCustomizer[TPage_contra], ABC):
    def _add_links_to_header(self, links: Links, /) -> None:
        parts = []
        for rel, link in (
            ("first", links.first),
            ("last", links.last),
            ("next", links.next),
            ("prev", links.prev),
        ):
            if link is not None:
                parts.append(f'<{link}>; rel="{rel}"')

        if parts:
            rsp = response()
            rsp.headers["Link"] = ", ".join(parts)

    def customize_page_ns(self, page_cls: PageCls, ns: ClsNamespace) -> None:
        def __model_post_init__(  # noqa: N807
            page_self: TPage_contra,
            _: Any,
        ) -> None:
            links = self.resolve_links(page_self)
            self._add_links_to_header(links)

        ns["model_post_init"] = __model_post_init__
