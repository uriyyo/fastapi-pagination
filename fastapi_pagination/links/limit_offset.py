from __future__ import annotations

__all__ = [
    "LimitOffsetPage",
    "UseLimitOffsetHeaderLinks",
    "UseLimitOffsetLinks",
    "resolve_limit_offset_links",
]

from abc import ABC
from collections.abc import Mapping
from math import floor
from typing import Any, TypeAlias

from typing_extensions import TypeVar

from fastapi_pagination.customization import CustomizedPage
from fastapi_pagination.limit_offset import LimitOffsetPage as BasePage

from .bases import BaseLinksCustomizer, BaseUseHeaderLinks, BaseUseLinks, Links, create_links

TAny = TypeVar("TAny", default=Any)


def resolve_limit_offset_links(_page: BasePage, /) -> Links:
    offset, limit, total = _page.offset, _page.limit, _page.total

    if offset is None:
        offset = 0

    last: Mapping[str, Any] | None = None
    if total is not None and limit is not None:
        # FIXME: it should not be so hard to calculate last page for limit-offset based pages
        start_offset = offset % limit
        last_offset = start_offset + floor((total - start_offset) / limit) * limit

        if last_offset == total:
            last_offset = total - limit

        # Fall back to the first page when this offset sequence has no valid page.
        last = {"offset": max(0, last_offset)}

    if total is not None:
        has_next = limit is not None and offset + limit < total
    elif limit is not None and hasattr(_page, "items") and _page.items is not None:
        has_next = len(_page.items) >= limit
    else:
        has_next = False

    has_prev = limit is not None and offset - limit >= 0

    return create_links(
        first={"offset": 0},
        last=last,
        next={"offset": offset + limit} if has_next else None,
        prev={"offset": offset - limit} if has_prev else None,
    )


class LimitOffsetLinksCustomizer(BaseLinksCustomizer, ABC):
    def resolve_links(self, _page: BasePage, /) -> Links:
        return resolve_limit_offset_links(_page)


class UseLimitOffsetLinks(LimitOffsetLinksCustomizer, BaseUseLinks):
    pass


class UseLimitOffsetHeaderLinks(LimitOffsetLinksCustomizer, BaseUseHeaderLinks):
    pass


LimitOffsetPage: TypeAlias = CustomizedPage[
    BasePage[TAny],
    UseLimitOffsetLinks(),
]
