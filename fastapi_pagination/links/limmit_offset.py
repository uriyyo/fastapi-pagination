from __future__ import annotations

from math import floor
from typing import Generic, Sequence, TypeVar

from ..bases import AbstractParams
from ..limit_offset import LimitOffsetPage as BasePage
from ..limit_offset import LimitOffsetParams
from .bases import Links, create_links

T = TypeVar("T")


class LimitOffsetPage(BasePage[T], Generic[T]):
    links: Links

    @classmethod
    def create(
        cls,
        items: Sequence[T],
        total: int,
        params: AbstractParams,
    ) -> LimitOffsetPage[T]:
        if not isinstance(params, LimitOffsetParams):
            raise ValueError("LimitOffsetPage should be used with LimitOffsetParams")

        next_link = None
        if params.offset + params.limit < total:
            next_link = {"offset": params.offset + params.limit}

        prev_link = None
        if 0 <= params.offset - params.limit:
            prev_link = {"offset": params.offset - params.limit}

        start_offset = params.offset % params.limit
        last = start_offset + floor((total - start_offset) / params.limit) * params.limit

        if last == total:
            last = total - params.limit

        return cls(
            total=total,
            items=items,
            limit=params.limit,
            offset=params.offset,
            links=create_links(
                first={"offset": 0},
                last={"offset": last},
                next=next_link,
                prev=prev_link,
            ),
        )


Page = LimitOffsetPage

__all__ = ["LimitOffsetPage", "Page"]
