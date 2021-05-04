from __future__ import annotations

from math import ceil
from typing import Any, Generic, TypeVar

from pydantic import root_validator

from ..default import Page as BasePage
from .bases import Links, create_links

T = TypeVar("T")


class Page(BasePage[T], Generic[T]):
    links: Links

    @root_validator(pre=True)
    def __root_validator__(cls, value: Any) -> Any:
        if "links" in value:
            return value

        page = value["page"]
        size = value["size"]
        total = value["total"]

        next_link = None
        if (page + 1) * size < total:
            next_link = {"page": page + 1}

        prev_link = None
        if 0 <= page - 1:
            prev_link = {"page": page - 1}

        value["links"] = create_links(
            first={"page": 0},
            last={"page": ceil(total / size)},
            next=next_link,
            prev=prev_link,
        )
        return value


__all__ = ["Page"]
