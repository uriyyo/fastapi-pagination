If you don't like default `Page` or `Params` you can always create your own.

## Page

In order to create custom `Page` you need to inherit from
`AbstractPage` and implement `create` classmethod.

```python
from __future__ import annotations
from typing import TypeVar, Generic, Sequence

from fastapi_pagination.bases import AbstractPage, AbstractParams
from fastapi_pagination import use_as_page

T = TypeVar("T")


@use_as_page
class Page(AbstractPage[T], Generic[T]):
    results: Sequence[T]

    @classmethod
    def create(
            cls,
            items: Sequence[T],
            total: int,
            params: AbstractParams,
    ) -> Page[T]:
        return cls(results=items)
```

Then it can be used in routes:

```python
@app.get("/", response_model=Page[User])
async def route():
    ...
```

## Params

To create a custom `PaginationParams` you should implement `AbstractParams`
protocol (it is not required to inherit from this cls).

`AbstractParams` protocol requires class to have `to_limit_offset` method that must return instance
of `fastapi_pagination.params.LimitOffsetPaginationParams` class.

```python
from pydantic import BaseModel

from fastapi_pagination.params import LimitOffsetPaginationParams
from fastapi_pagination import using_params


class Params(BaseModel):
    total_items: int
    return_per_page: int

    def to_limit_offset(self) -> LimitOffsetPaginationParams:
        return LimitOffsetPaginationParams(
            limit=self.total_items,
            offset=self.total_items * self.return_per_page,
        )


pagination_params = using_params(Params)
```

Then custom params can be used in two ways:

1. Using implicit params.

    ```python
    @app.get(
        "/",
        response_model=Page[UserOut],
        dependencies=[Depends(pagination_params)],
    )
    async def route():
        # In this case not need to pass params to paginator
        return await paginate(User)
    ```

    ```python
    @app.get(
        "/",
        response_model=Page[UserOut],
    )
    async def route(params: Params = Depends(pagination_params)):
        # In this case not need to pass params to paginator
        return await paginate(User)
    ```

2. Using explicit params.

    ```python
    @app.route(
        "/",
        response_model=Page[UserOut],
    )
    async def bar(params: Params):
        # In this case params must be passed to paginator
        return await paginate(User, params)
    ```
