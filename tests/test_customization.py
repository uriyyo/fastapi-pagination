from typing import ClassVar, Generic, Type, TypeVar

from fastapi import Query
from pytest import mark, raises

from fastapi_pagination import Page, Params
from fastapi_pagination.bases import AbstractPage, AbstractParams
from fastapi_pagination.customization import (
    ClsNamespace,
    CustomizePage,
    PageCustomizer,
    UseIncludeTotal,
    UseModule,
    UseName,
    UseOptionalParams,
    UseParams,
    UseParamsFields,
)


class _NoopCustomizer(PageCustomizer):
    def customize_page_ns(self, page_cls: Type[AbstractPage], ns: ClsNamespace) -> None:
        pass


def test_customization_happy_path():
    _ = CustomizePage[
        Page,
        UseName("CustomPage"),
        UseModule("custom_module"),
        UseParams(Params),
        UseIncludeTotal(False),
        UseParamsFields(page=10),
        UseOptionalParams(),
    ]

    _ = CustomizePage[
        Page[int],
        UseName("IntPage"),
    ]


def test_customization_no_args():
    assert CustomizePage[Page] is Page


def test_customization_incorrect_customizer():
    with raises(TypeError, match="^Expected PageCustomizer, got .*$"):
        _ = CustomizePage[Page, object()]


def test_customization_use_name():
    CustomPage = CustomizePage[Page, UseName("CustomPage")]

    assert CustomPage.__name__ == "CustomPage"
    assert CustomPage.__qualname__ == "CustomPage"


def test_customization_use_module():
    CustomPage = CustomizePage[Page, UseModule("custom_module")]

    assert CustomPage.__module__ == "custom_module"


def test_customization_default_module():
    CustomPage = CustomizePage[Page, _NoopCustomizer()]

    assert CustomPage.__module__ == __name__


def test_customization_use_params():
    class CustomParams(AbstractParams):
        pass

    CustomPage = CustomizePage[Page, UseParams(CustomParams)]

    assert CustomPage.__params_type__ is CustomParams


def test_customization_use_params_after_use_include_total():
    class CustomParams(AbstractParams):
        pass

    with raises(ValueError, match=r"^Params type was already customized, cannot customize it again\..*$"):
        _ = CustomizePage[Page, UseIncludeTotal(True), UseParams(CustomParams)]


def test_customization_use_params_fields():
    CustomPage = CustomizePage[Page, UseParamsFields(page=10, size=20)]

    params = CustomPage.__params_type__()

    assert params.page == 10
    assert params.size == 20


def test_customization_use_unknown_field():
    with raises(ValueError, match="^Unknown field unknown_field$"):
        _ = CustomizePage[Page, UseParamsFields(unknown_field=10)]

    with raises(ValueError, match="^Unknown fields a, b$"):
        _ = CustomizePage[Page, UseParamsFields(a=10, b=1)]


def test_customization_use_query_field():
    CustomPage = CustomizePage[Page, UseParamsFields(page=Query(10), size=Query(20))]

    params = CustomPage.__params_type__()

    assert params.page == 10
    assert params.size == 20


def test_customization_update_class_var():
    class _Params(Page.__params_type__):
        var: ClassVar[int] = 10

    T = TypeVar("T")

    class _Page(Page[T], Generic[T]):
        __params_type__ = _Params

    CustomPage = CustomizePage[_Page, UseParamsFields(var=20)]

    assert CustomPage.__params_type__.var == 20


def test_customization_use_params_fields_non_pydantic_params():
    T = TypeVar("T")

    class CustomPage(Page[T]):
        __params_type__ = object

    with raises(TypeError, match="^.* must be subclass of BaseModel$"):
        _ = CustomizePage[CustomPage, UseParamsFields(page=10, size=20)]


def test_customize_use_optional_params():
    CustomPage = CustomizePage[Page, UseOptionalParams()]

    params = CustomPage.__params_type__()

    assert params.page is None
    assert params.size is None


@mark.parametrize("include_total", [True, False])
def test_use_include_total(include_total):
    CustomPage = CustomizePage[Page, UseIncludeTotal(include_total)]
    raw_params = CustomPage.__params_type__().to_raw_params()

    assert raw_params.include_total == include_total


def test_custom_customizer():
    class CustomCustomizer(PageCustomizer):
        def customize_page_ns(self, page_cls: Type[AbstractPage], ns: ClsNamespace) -> None:
            ns["__customized__"] = True

    CustomPage = CustomizePage[Page, CustomCustomizer()]
    assert CustomPage.__customized__ is True
