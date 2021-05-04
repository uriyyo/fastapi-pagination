from __future__ import annotations

from math import ceil
from typing import Generic, Sequence, TypeVar

from ..bases import AbstractParams
from ..default import Page as BasePage
from ..default import Params
from .bases import Links, create_links

T = TypeVar("T")


class Page(BasePage[T], Generic[T]):
    links: Links

    @classmethod
    def create(
        cls,
        items: Sequence[T],
        total: int,
        params: AbstractParams,
    ) -> Page[T]:
        if not isinstance(params, Params):
            raise ValueError("Page should be used with Params")

        next_link = None
        if (params.page + 1) * params.size < total:
            next_link = {"page": params.page + 1}

        prev_link = None
        if 0 <= (params.page - 1):
            prev_link = {"page": params.page - 1}

        return cls(
            total=total,
            items=items,
            page=params.page,
            size=params.size,
            links=create_links(
                first={"page": 0},
                last={"page": ceil(total / params.size)},
                next=next_link,
                prev=prev_link,
            ),
        )


__all__ = ["Page"]
