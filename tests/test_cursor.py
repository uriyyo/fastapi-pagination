from pytest import raises

from fastapi_pagination import paginate
from fastapi_pagination.cursor import CursorParams


def test_unsupported_params():

    with raises(ValueError, match="^'cursor' params not supported$"):
        paginate([1, 2, 3], CursorParams())
