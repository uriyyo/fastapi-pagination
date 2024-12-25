from typing import Generic, Optional, TypeVar

import pytest
from fastapi import Query

from fastapi_pagination import Page, Params
from fastapi_pagination.cursor import CursorParams

T = TypeVar("T")
C = TypeVar("C")


def test_zero_size():
    class CustomParams(Params):
        size: Optional[int] = Query(0)

    class CustomPage(Page[T], Generic[T]):
        size: Optional[int] = None

        __params_type__ = CustomParams

    res = CustomPage[int].create(
        [],
        CustomParams(),
        total=0,
    )

    assert res.dict() == {
        "items": [],
        "page": 1,
        "pages": 0,
        "size": 0,
        "total": 0,
    }


def test_invalid_params_cast():
    with pytest.raises(ValueError, match="^Not a 'limit-offset' params$"):
        CursorParams().to_raw_params().as_limit_offset()

    with pytest.raises(ValueError, match="^Not a 'cursor' params$"):
        Params().to_raw_params().as_cursor()


def test_params_cast():
    p = CursorParams().to_raw_params()

    assert p.as_cursor() is p

    p = Params().to_raw_params()

    assert p.as_limit_offset() is p
