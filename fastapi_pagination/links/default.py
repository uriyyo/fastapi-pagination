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
        if "links" not in value:
            page, size, total = [value[k] for k in ("page", "size", "total")]

            value["links"] = create_links(
                first={"page": 0},
                last={"page": ceil(total / size)},
                next={"page": page + 1} if (page + 1) * size < total else None,
                prev={"page": page - 1} if 0 <= page - 1 else None,
            )

        return value


__all__ = ["Page"]
