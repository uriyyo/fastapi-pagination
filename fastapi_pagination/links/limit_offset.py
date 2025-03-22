from __future__ import annotations

__all__ = [
    "LimitOffsetPage",
    "UseLimitOffsetLinks",
    "resolve_limit_offset_links",
]

from math import floor, inf
from typing import Any, cast

from typing_extensions import TypeAlias, TypeVar

from fastapi_pagination.customization import CustomizedPage
from fastapi_pagination.limit_offset import LimitOffsetPage as BasePage

from .bases import BaseUseLinks, Links, create_links

TAny = TypeVar("TAny", default=Any)


def resolve_limit_offset_links(_page: BasePage, /) -> Links:
    offset, limit, total = _page.offset, _page.limit, _page.total

    if offset is None:
        offset = 0
    if limit is None:
        limit = cast(int, inf)
    if total is None:
        total = cast(int, inf)

    # FIXME: it should not be so hard to calculate last page for limit-offset based pages
    start_offset = offset % limit
    last = start_offset + floor((total - start_offset) / limit) * limit

    if last == total:
        last = total - limit

    return create_links(
        first={"offset": 0},
        last={"offset": last},
        next={"offset": offset + limit} if offset + limit < total else None,
        prev={"offset": offset - limit} if offset - limit >= 0 else None,
    )


class UseLimitOffsetLinks(BaseUseLinks):
    def resolve_links(self, _page: BasePage, /) -> Links:
        return resolve_limit_offset_links(_page)


LimitOffsetPage: TypeAlias = CustomizedPage[
    BasePage[TAny],
    UseLimitOffsetLinks(),
]
