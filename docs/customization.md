If you don't like default `Page` or `Params` you can always create your own.

## Page

In order to create custom `Page` you need to inherit from
`AbstractPage` and implement `create` classmethod.

```python
from __future__ import annotations
from typing import TypeVar, Generic, Sequence

from fastapi_pagination import Params
from fastapi_pagination.bases import AbstractPage, AbstractParams

T = TypeVar("T")


class Page(AbstractPage[T], Generic[T]):
    results: Sequence[T]

    __params_type__ = Params  # Set params related to Page

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

To create a custom `Params` you should inherit from `AbstractParams` and implement
`to_raw_params` method.

```python
from pydantic import BaseModel

from fastapi_pagination.bases import RawParams, AbstractParams


class Params(BaseModel, AbstractParams):
    total_items: int
    return_per_page: int

    def to_raw_params(self) -> RawParams:
        return RawParams(
            limit=self.total_items,
            offset=self.total_items * self.return_per_page,
        )
```

## Custom Params values

```python
from typing import TypeVar, Generic

from fastapi import Query

from fastapi_pagination.default import Page as BasePage, Params as BaseParams

T = TypeVar("T")


class Params(BaseParams):
    size: int = Query(500, gt=0, le=1_000, description="Page size")


class Page(BasePage[T], Generic[T]):
    __params_type__ = Params
```