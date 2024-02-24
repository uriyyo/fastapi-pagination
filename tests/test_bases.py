import re
from typing import ClassVar, Generic, Optional, Sequence, TypeVar

from fastapi import FastAPI, Query, status
from fastapi.testclient import TestClient
from pytest import mark, raises, warns

from fastapi_pagination import Page, Params, add_pagination, paginate
from fastapi_pagination.bases import AbstractParams, RawParams
from fastapi_pagination.cursor import CursorParams

T = TypeVar("T")
C = TypeVar("C")


def test_custom_page_invalid_params_cls():
    class CustomParams(AbstractParams):
        def to_raw_params(self) -> RawParams:
            return RawParams(0, 0)

    class CustomPage(Page[T], Generic[T]):
        __params_type__ = CustomParams

    with raises(TypeError, match="^CustomParams must be subclass of BaseModel$"):
        CustomPage.with_custom_options(size=10)


def test_custom_page_invalid_values():
    with raises(ValueError, match="^Unknown field smth_wrong$"):
        Page.with_custom_options(smth_wrong=100)

    with raises(ValueError, match="^Unknown fields a, b, c"):
        Page.with_custom_options(a=1, b=2, c=3)


class MultipleParamsPage(Page[T], Generic[T, C]):
    sub_items: Sequence[C]


@mark.parametrize(
    "cls",
    [Page, Page[int], MultipleParamsPage],
    ids=["non-concrete", "concrete", "non-concrete-multiple-params"],
)
def test_custom_page(cls):
    page_cls = cls.with_custom_options()
    assert page_cls.__params_type__().dict() == {"size": 50, "page": 1}

    page_cls = cls.with_custom_options(size=100)
    assert page_cls.__params_type__().dict() == {"size": 100, "page": 1}

    page_cls = cls.with_custom_options(size=100, page=100)
    assert page_cls.__params_type__().dict() == {"size": 100, "page": 100}


def test_with_custom_options_class_vars():
    class CustomParams(Params):
        class_var: ClassVar[bool] = False

    class CustomPage(Page[T], Generic[T]):
        __params_type__ = CustomParams

    assert CustomPage.__params_type__.class_var is False

    customized_page = CustomPage.with_custom_options(class_var=True)
    assert customized_page.__params_type__.class_var is True


def test_with_custom_options_items_casted():
    page_cls = Page.with_custom_options(size=10, page=2)

    res = page_cls[int].create(
        [1, 2.0, "3", b"4", 5],
        page_cls.__params_type__(),
        total=100,
    )

    assert res.dict() == {
        "items": [1, 2, 3, 4, 5],
        "page": 2,
        "pages": 10,
        "size": 10,
        "total": 100,
    }


def test_with_custom_options_wrap_into_query():
    app = FastAPI()
    client = TestClient(app)

    page_cls = Page.with_custom_options(size=10, page=Query(2))

    @app.get(
        "/",
        response_model=page_cls[int],
    )
    async def route():
        return paginate([])

    add_pagination(app)

    rsp = client.get("/", params={"page": 3, "size": 5})
    assert rsp.status_code == status.HTTP_200_OK


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
    with raises(ValueError, match="^Not a 'limit-offset' params$"):
        CursorParams().to_raw_params().as_limit_offset()

    with raises(ValueError, match="^Not a 'cursor' params$"):
        Params().to_raw_params().as_cursor()


def test_params_cast():
    p = CursorParams().to_raw_params()

    assert p.as_cursor() is p

    p = Params().to_raw_params()

    assert p.as_limit_offset() is p


def test_deprecated_signature():
    massage = re.compile(
        r"^The signature of the `AbstractPage\.create` method has changed\. Please, update it to the new one\. "
        r"\(items: 'Sequence\[T\]', params: 'AbstractParams', \*\*kwargs: 'Any'\) \-\> 'Type'"
        r"\nSupport of old signature will be removed in the next major release \(0\.13\.0\)\.$",
        re.DOTALL | re.MULTILINE,
    )

    # old signature
    with warns(DeprecationWarning, match=massage):

        class P1(Page[T], Generic[T]):
            @classmethod
            def create(
                cls,
                items: Sequence[T],
                total: Optional[int],
                params: AbstractParams,
            ) -> Page[T]:
                pass

    # no kwargs
    with warns(DeprecationWarning, match=massage):

        class P2(Page[T], Generic[T]):
            @classmethod
            def create(
                cls,
                items: Sequence[T],
                params: AbstractParams,
            ) -> Page[T]:
                pass

    # positional only
    with warns(DeprecationWarning, match=massage):

        class P3(Page[T], Generic[T]):
            @classmethod
            def create(
                cls,
                items: Sequence[T],
                /,
                params: AbstractParams,
                **kwargs,
            ) -> Page[T]:
                pass

    # positional var
    with warns(DeprecationWarning, match=massage):

        class P4(Page[T], Generic[T]):
            @classmethod
            def create(
                cls,
                items: Sequence[T],
                params: AbstractParams,
                *args,
                **kwargs,
            ) -> Page[T]:
                pass

    # keyword only no default
    with warns(DeprecationWarning, match=massage):

        class P5(Page[T], Generic[T]):
            @classmethod
            def create(
                cls,
                items: Sequence[T],
                params: AbstractParams,
                *,
                total: int,
                **kwargs,
            ) -> Page[T]:
                pass

    # wrong params
    with warns(DeprecationWarning, match=massage):

        class P6(Page[T], Generic[T]):
            @classmethod
            def create(
                cls,
                data: Sequence[T],
                params: AbstractParams,
                **kwargs,
            ) -> Page[T]:
                pass

    # not a classmethod
    with warns(DeprecationWarning, match=massage):

        class P7(Page[T], Generic[T]):
            def create(
                cls,
                data: Sequence[T],
                params: AbstractParams,
                **kwargs,
            ) -> Page[T]:
                pass
