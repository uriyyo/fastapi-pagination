from typing import ClassVar, Generic, TypeVar

import pytest
from fastapi import FastAPI, Query, status

from fastapi_pagination import Page, Params, add_pagination, paginate
from fastapi_pagination.bases import AbstractPage, AbstractParams
from fastapi_pagination.cursor import CursorPage, encode_cursor
from fastapi_pagination.customization import (
    ClsNamespace,
    CustomizedPage,
    PageCustomizer,
    UseAdditionalFields,
    UseCursorEncoding,
    UseExcludedFields,
    UseFieldsAliases,
    UseIncludeTotal,
    UseModelConfig,
    UseModule,
    UseName,
    UseOptionalParams,
    UseParams,
    UseParamsFields,
    UsePydanticV1,
    UseQuotedCursor,
    UseResponseHeaders,
    UseStrCursor,
)
from fastapi_pagination.pydantic import IS_PYDANTIC_V2
from fastapi_pagination.pydantic.v1 import BaseModelV1


class _NoopCustomizer(PageCustomizer):
    def customize_page_ns(self, page_cls: type[AbstractPage], ns: ClsNamespace) -> None:
        pass


def test_customization_happy_path():
    _ = CustomizedPage[
        Page,
        UseName("CustomPage"),
        UseModule("custom_module"),
        UseParams(Params),
        UseIncludeTotal(False),
        UseParamsFields(page=10),
        UseOptionalParams(),
    ]

    _ = CustomizedPage[
        Page[int],
        UseName("IntPage"),
    ]


def test_customization_double():
    First = CustomizedPage[
        Page,
        UseModule("first"),
    ]

    Second = CustomizedPage[
        First,
        UseModule("second"),
    ]

    assert Second.__name__ == "PageCustomized"


def test_customization_no_args():
    assert CustomizedPage[Page] is Page


def test_customization_incorrect_customizer():
    with pytest.raises(TypeError, match=r"^Expected PageCustomizer or PageTransformer, got .*$"):
        _ = CustomizedPage[Page, object()]


def test_customization_use_name():
    CustomPage = CustomizedPage[Page, UseName("CustomPage")]

    assert CustomPage.__name__ == "CustomPage"
    assert CustomPage.__qualname__ == "CustomPage"


def test_customization_use_module():
    CustomPage = CustomizedPage[Page, UseModule("custom_module")]

    assert CustomPage.__module__ == "custom_module"


def test_customization_default_module():
    CustomPage = CustomizedPage[Page, _NoopCustomizer()]

    assert CustomPage.__module__ == __name__


def test_customization_use_params():
    class CustomParams(AbstractParams):
        pass

    CustomPage = CustomizedPage[Page, UseParams(CustomParams)]

    assert issubclass(CustomPage.__params_type__, CustomParams)


def test_customization_use_params_after_use_include_total():
    class CustomParams(AbstractParams):
        pass

    with pytest.raises(ValueError, match=r"^Params type was already customized, cannot customize it again\..*$"):
        _ = CustomizedPage[Page, UseIncludeTotal(True), UseParams(CustomParams)]


def test_customization_use_params_fields():
    CustomPage = CustomizedPage[Page, UseParamsFields(page=10, size=20)]

    params = CustomPage.__params_type__()

    assert params.page == 10
    assert params.size == 20


def test_customization_use_unknown_field():
    with pytest.raises(ValueError, match=r"^Unknown field unknown_field$"):
        _ = CustomizedPage[Page, UseParamsFields(unknown_field=10)]

    with pytest.raises(ValueError, match=r"^Unknown fields a, b$"):
        _ = CustomizedPage[Page, UseParamsFields(a=10, b=1)]


def test_customization_use_query_field():
    CustomPage = CustomizedPage[Page, UseParamsFields(page=Query(10), size=Query(20))]

    params = CustomPage.__params_type__()

    assert params.page == 10
    assert params.size == 20


def test_customization_update_class_var():
    class _Params(Page.__params_type__):
        var: ClassVar[int] = 10

    T = TypeVar("T")

    class _Page(Page[T], Generic[T]):
        __params_type__ = _Params

    CustomPage = CustomizedPage[_Page, UseParamsFields(var=20)]

    assert CustomPage.__params_type__.var == 20


def test_customization_use_params_fields_non_pydantic_params():
    T = TypeVar("T")

    class CustomPage(Page[T]):
        __params_type__ = object

    with pytest.raises(TypeError, match=r"^.* must be subclass of BaseModel$"):
        _ = CustomizedPage[CustomPage, UseParamsFields(page=10, size=20)]


def test_customize_use_optional_params():
    CustomPage = CustomizedPage[Page, UseOptionalParams()]

    params = CustomPage.__params_type__()

    assert params.page is None
    assert params.size is None


@pytest.mark.parametrize("include_total", [True, False])
def test_use_include_total(include_total):
    CustomPage = CustomizedPage[Page, UseIncludeTotal(include_total)]
    raw_params = CustomPage.__params_type__().to_raw_params()

    assert raw_params.include_total == include_total


@pytest.mark.skipif(not IS_PYDANTIC_V2, reason="Only for Pydantic v2")
@pytest.mark.parametrize("include_total", [True, False])
def test_use_include_total_update_tp_json_schema(include_total):
    app = FastAPI()

    CustomPage = CustomizedPage[Page, UseIncludeTotal(include_total)]

    @app.get("/", response_model=CustomPage)
    def root():
        return None

    total_schema = app.openapi()["components"]["schemas"]["PageCustomized"]["properties"]["total"]

    if include_total:
        assert total_schema == {"minimum": 0.0, "title": "Total", "type": "integer"}
    else:
        assert total_schema == {"anyOf": [{"minimum": 0.0, "type": "integer"}, {"type": "null"}], "title": "Total"}


@pytest.mark.parametrize("quoted_cursor", [True, False])
def test_use_quoted_cursor(quoted_cursor):
    CustomPage = CustomizedPage[Page, UseQuotedCursor(quoted_cursor)]

    assert CustomPage.__params_type__.quoted_cursor == quoted_cursor


def test_custom_customizer():
    class CustomCustomizer(PageCustomizer):
        def customize_page_ns(self, page_cls: type[AbstractPage], ns: ClsNamespace) -> None:
            ns["__customized__"] = True

    CustomPage = CustomizedPage[Page, CustomCustomizer()]
    assert CustomPage.__customized__ is True


def test_use_model_config():
    key = "populate_by_name" if IS_PYDANTIC_V2 else "allow_population_by_field_name"

    CustomPage = CustomizedPage[
        Page,
        UseModelConfig(**{key: False}),
    ]

    if IS_PYDANTIC_V2:
        assert CustomPage.model_config["populate_by_name"] is False
    else:
        assert CustomPage.__config__.allow_population_by_field_name is False


def test_use_excluded_fields():
    CustomPage = CustomizedPage[
        Page,
        UseExcludedFields("total"),
    ]

    if IS_PYDANTIC_V2:
        assert CustomPage.model_fields["total"].exclude
    else:
        assert "total" in CustomPage.__exclude_fields__


def test_use_aliases():
    CustomPage = CustomizedPage[
        Page,
        UseFieldsAliases(total="count"),
    ]

    if IS_PYDANTIC_V2:
        assert CustomPage.model_fields["total"].serialization_alias == "count"
    else:
        assert CustomPage.__fields__["total"].alias == "count"


def test_additional_fields():
    CustomPage = CustomizedPage[
        Page,
        UseAdditionalFields(
            a=int,
            b=(str, "my-default"),
        ),
    ]

    if IS_PYDANTIC_V2:
        from pydantic_core import PydanticUndefined

        assert CustomPage.model_fields["a"].annotation is int
        assert CustomPage.model_fields["a"].default is PydanticUndefined

        assert CustomPage.model_fields["b"].annotation is str
        assert CustomPage.model_fields["b"].default == "my-default"
    else:
        assert CustomPage.__fields__["a"].type_ is int
        assert CustomPage.__fields__["a"].default is None

        assert CustomPage.__fields__["b"].type_ is str
        assert CustomPage.__fields__["b"].default == "my-default"


@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {"encoder": lambda *_: "encoded"},
        {"decoder": lambda *_: "decoded"},
        {"encoder": lambda *_: "encoded", "decoder": lambda *_: "decoded"},
    ],
    ids=[
        "no_encoder_decoder",
        "encoder",
        "decoder",
        "encoder_decoder",
    ],
)
def test_cursor_encoding(kwargs):
    CustomPage = CustomizedPage[
        CursorPage,
        UseCursorEncoding(**kwargs),
    ]

    page = CustomPage.create([], CustomPage.__params_type__(), total=0, current="current")

    if "encoder" in kwargs:
        assert page.current_page == "encoded"
    else:
        assert page.current_page == encode_cursor("current")

    decoded = CustomPage.__params_type__().decode_cursor(encode_cursor("current"))

    if "decoder" in kwargs:
        assert decoded == "decoded"
    else:
        assert decoded == "current"


@pytest.mark.parametrize("str_cursor", [True, False])
def test_str_cursor(str_cursor):
    CustomPage = CustomizedPage[
        CursorPage,
        UseStrCursor(str_cursor),
    ]

    assert CustomPage.__params_type__.str_cursor == str_cursor


@pytest.mark.skipif(
    not IS_PYDANTIC_V2,
    reason="UseResponseHeaders is only supported in Pydantic v2",
)
class TestUseResponseHeaders:
    @pytest.fixture(scope="session")
    def app(self):
        _app = FastAPI()
        add_pagination(_app)

        CustomPage = CustomizedPage[
            Page,
            UseResponseHeaders(
                lambda page: {
                    "X-Total-Count": str(page.total or 0),
                    "X-Params": [
                        f"page={page.page}",
                        f"size={page.size}",
                    ],
                }
            ),
        ]

        @_app.get("/items")
        def _items() -> CustomPage[int]:
            return paginate([*range(100)])

        return _app

    @pytest.mark.asyncio
    async def test_response_headers(self, client):
        response = await client.get("/items", params={"page": 2, "size": 20})

        assert response.status_code == status.HTTP_200_OK
        assert response.headers["X-Total-Count"] == "100"
        assert response.headers.get_list("X-Params") == ["page=2", "size=20"]


def test_use_pydantic_v1():
    CustomPage = CustomizedPage[
        Page,
        UsePydanticV1(),
    ]

    assert issubclass(CustomPage, BaseModelV1)

    page = CustomPage[int].create(
        items=["1", "2", "3"],
        params=CustomPage.__params_type__(),
        total=3,
    )

    assert page.items == [1, 2, 3]
    assert page.total == 3
