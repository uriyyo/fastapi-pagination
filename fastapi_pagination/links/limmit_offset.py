from __future__ import annotations

from math import floor
from typing import Any, Generic, TypeVar

from pydantic import root_validator

from ..limit_offset import LimitOffsetPage as BasePage
from .bases import Links, create_links

T = TypeVar("T")


class LimitOffsetPage(BasePage[T], Generic[T]):
    links: Links

    @root_validator(pre=True)
    def __root_validator__(cls, value: Any) -> Any:
        if "links" in value:
            return value

        total = value["total"]
        offset = value["offset"]
        limit = value["limit"]

        next_link = None
        if offset + limit < total:
            next_link = {"offset": offset + limit}

        prev_link = None
        if offset - limit >= 0:
            prev_link = {"offset": offset - limit}

        start_offset = offset % limit
        last = start_offset + floor((total - start_offset) / limit) * limit

        if last == total:
            last = total - limit

        value["links"] = create_links(
            first={"offset": 0},
            last={"offset": last},
            next=next_link,
            prev=prev_link,
        )

        return value


Page = LimitOffsetPage

__all__ = ["LimitOffsetPage", "Page"]
