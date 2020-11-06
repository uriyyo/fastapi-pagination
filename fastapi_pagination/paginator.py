from typing import TypeVar

from fastapi_pagination.page import create_page, BasePage
from fastapi_pagination.params import PaginationParamsType
from sqlalchemy import Sequence

T = TypeVar("T")


def paginate(sequence: Sequence[T], params: PaginationParamsType) -> BasePage[T]:
    params = params.to_limit_offset()

    return create_page(
        items=sequence[params.offset : params.offset + params.limit],
        total=len(sequence),
        params=params,
    )


__all__ = ["paginate"]
