from typing import Sequence, TypeVar

from fastapi_pagination.page import BasePage, create_page
from fastapi_pagination.params import PaginationParamsType

T = TypeVar("T")


def paginate(sequence: Sequence[T], params: PaginationParamsType) -> BasePage[T]:
    params = params.to_limit_offset()

    return create_page(
        items=sequence[params.offset : params.offset + params.limit],
        total=len(sequence),
        params=params,
    )


__all__ = ["paginate"]
