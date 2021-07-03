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
                first={"page": 1},
                last={"page": ceil(total / size) if total > 0 else 1},
                next={"page": page + 1} if page * size < total else None,
                prev={"page": page - 1} if 1 <= page - 1 else None,
            )

        return value


__all__ = ["Page"]
