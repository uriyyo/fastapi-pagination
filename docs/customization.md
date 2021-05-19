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

### JSON:API custom Page example

To extend the default Page with additional params, like the [JSON:API](https://jsonapi.org) 
schema, try the example below:

```python
from __future__ import annotations

from math import ceil
from typing import Any, Generic, Sequence, TypeVar

from fastapi_pagination import Params
from fastapi_pagination.bases import AbstractPage, AbstractParams
from fastapi_pagination.links.bases import Links, create_links

from pydantic import conint
from pydantic import root_validator


T = TypeVar("T")


class JsonApiPage(AbstractPage[T], Generic[T]):
    """JSON:API 1.0 specification says that result key should be a `data`."""

    total: conint(ge=0)  # type: ignore
    page: conint(ge=0)  # type: ignore
    size: conint(gt=0)  # type: ignore
    data: Sequence[T]
    links: Links

    __params_type__ = Params  # Set params related to Page

    @classmethod
    def create(
        cls, items: Sequence[T], total: int, params: AbstractParams
    ) -> JsonApiPage[T]:
        """Same as the original Page.create instead of `data`."""
        if not isinstance(params, Params):
            raise ValueError("Page should be used with Params")

        return cls(total=total, data=items, page=params.page, size=params.size)

    @root_validator(pre=True)
    def __root_validator__(cls, value: Any) -> Any:
        """Pagination links builder."""
        if "links" not in value:
            page, size, total = [value[k] for k in ("page", "size", "total")]

            value["links"] = create_links(
                first={"page": 0},
                last={"page": ceil(total / size) - 1},
                next={"page": page + 1} if (page + 1) * size < total else None,
                prev={"page": page - 1} if 0 <= page - 1 else None,
            )

        return value
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