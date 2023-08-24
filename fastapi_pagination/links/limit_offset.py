from __future__ import annotations

__all__ = ["LimitOffsetPage"]

from math import floor
from typing import Any, Generic, MutableMapping, TypeVar

from ..limit_offset import LimitOffsetPage as BasePage
from .bases import Links, create_links, validation_decorator

T = TypeVar("T")


class LimitOffsetPage(BasePage[T], Generic[T]):
    links: Links

    @validation_decorator
    def __root_validator__(cls, value: Any) -> Any:
        if not isinstance(value, MutableMapping):
            return value

        if "links" not in value:
            offset, limit, total = [value[k] for k in ("offset", "limit", "total")]

            # FIXME: it should not be so hard to calculate last page for limit-offset based pages
            start_offset = offset % limit
            last = start_offset + floor((total - start_offset) / limit) * limit

            if last == total:
                last = total - limit

            value["links"] = create_links(
                first={"offset": 0},
                last={"offset": last},
                next={"offset": offset + limit} if offset + limit < total else None,
                prev={"offset": offset - limit} if offset - limit >= 0 else None,
            )

        return value
