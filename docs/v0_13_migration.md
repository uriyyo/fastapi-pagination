# Python version support

Now the minimum supported Python version is `3.9`.

# Paginate function

Starting from version `0.13.0`, the async `paginate` function has been renamed to `apaginate` to avoid confusion with the sync version
and follow better naming conventions. Old code using `paginate` will still work, but it is recommended to update your code to use `apaginate` for async operations.
Support for `async` calls for `paginate` will be removed in the next major version.

# API Changes

## `create_page`

`create_page` function no longer accepts `total` and `params` arguments as positional.
Instead, it accepts `total` and `params` as keyword arguments.

## `Page.create`

`Page.create` class method signature was changed. Now it accepts `total` only as a keyword argument.
It was changed because `total` is no longer a required argument and can be omitted in some cases.

New signature now looks like this:
```python
    @classmethod
    def create(
        cls,
        items: Sequence[T],
        params: AbstractParams,
        **kwargs: Any,
    ) -> Self:
        pass
```

## `Page.with_params`/`Page.with_custom_options`

`Page.with_params` and `Page.with_custom_options` class methods where removed.
Now you need to use `CustomizedPage` class to create a new page object with custom options.

`Page.with_params` migration:
```python
from typing import TypeVar

from fastapi_pagination import Page, Params
from fastapi_pagination.customization import CustomizedPage, UseParams

T = TypeVar("T")

class MyParams(Params):
    ...

# CustomPage = Page.with_params(MyParams)
CustomPage = CustomizedPage[
    Page[T],
    UseParams(MyParams),
]
```

`Page.with_custom_options` migration:
```python
from typing import TypeVar

from fastapi import Query

from fastapi_pagination import Page
from fastapi_pagination.customization import CustomizedPage, UseParamsFields

T = TypeVar("T")

# CustomPage = Page.with_custom_options(size=Query(100, ge=1, le=1000))
CustomPage = CustomizedPage[
    Page[T],
    UseParamsFields(size=Query(100, ge=1, le=1000)),
]
```

`cls_name`, `module` args migration:
```python
from typing import TypeVar

from fastapi import Query

from fastapi_pagination import Page
from fastapi_pagination.customization import CustomizedPage, UseName, UseModule, UseParamsFields

T = TypeVar("T")

# CustomPage = Page.with_custom_options(
#     size=Query(100, ge=1, le=1000),
#     cls_name="CustomPage",
#     module="my_module"
# )
CustomPage = CustomizedPage[
    Page[T],
    UseName("CustomPage"),
    UseModule("my_module"),
    UseParamsFields(size=Query(100, ge=1, le=1000)),
]
```

## `OptionalParams`/`OptionalLimitOffsetParams`

`OptionalParams`/`OptionalLimitOffsetParams` classes were removed. Now you need to use `UseOptionalParams` customization:

```python
from typing import TypeVar

from fastapi_pagination import Page
from fastapi_pagination.customization import CustomizedPage, UseOptionalParams

T = TypeVar("T")

CustomPage = CustomizedPage[
    Page[T],
    UseOptionalParams(),
]
```

# Extension Changes

## `fastapi_pagination.ext.sqlalchemy`

`paginate_query` function was removed. Now you need to use `create_paginate_query` function:

```python
from fastapi_pagination.ext.sqlalchemy import create_paginate_query
```

# Removed modules

The following modules have been removed from the library:

* `fastapi_pagination.ext.async_sqlalchemy`
* `fastapi_pagination.ext.sqlalchemy_future`
* `fastapi_pagination.ext.async_sqlmodel`

If you were using any of these modules, you will need to update your code to use the `fastapi_pagination.ext.sqlalchemy` module
for SQLAlchemy and `fastapi_pagination.ext.sqlmodel` module for SQLModel.
