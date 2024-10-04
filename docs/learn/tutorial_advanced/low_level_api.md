from fastapi_pagination.bases import AbstractParamsThis page describes the low-level API from `fastapi_pagination.api` module.

## `add_pagination`

`add_pagination` is a function that allows to add pagination support to a FastAPI application.
It accepts a FastAPI application instance as an argument and returns the same instance with pagination support.
It will modify all routes that return a `Page` instance to return a paginated response.

```py
from fastapi import FastAPI
from fastapi_pagination.api import add_pagination

app = FastAPI()
add_pagination(app)  # that's all folks!
```

## `pagination_ctx`

`pagination_ctx` is a function that allows to set a page context for route, it accepts page type, params type and
items transformer as arguments.

```py
from fastapi import FastAPI, Depends
from fastapi_pagination import Page, Params, paginate
from fastapi_pagination.api import pagination_ctx

app = FastAPI()

# req: GET /users?page=2&size=10
@app.get(
    "/users",
    dependencies=[
        Depends(
            pagination_ctx(
                page=Page[int],
                params=Params,
                transformer=lambda items: [x * 2 for x in items],
            ),
        ),
    ]
)
async def get_users():
    return paginate(range(100))
```

## `set_page`

`set_page` is a function that allows to set a page type for pagination.
It also can be used as a context manager to set a page type for a specific context.

```py
from fastapi_pagination import Page
from fastapi_pagination.api import set_page

# set global page type
set_page(Page[int])

# set page type for a specific context
with set_page(Page[str]):
    pass
```

## `create_page`

`create_page` is a function that allows to create a new page instance. It will take current page type from `set_page`
function or use `Page` class as a default page type. `create_page` function accepts 1 required argument `items`,
1 required keyword argument `params` and 1 optional keyword argument `total`.

```py
from fastapi_pagination import Page, Params
from fastapi_pagination.api import set_page, create_page

set_page(Page[int])

page = create_page([1, 2, 3], params=Params(page=1, size=3), total=1_000_000)

print(page.model_dump_json(indent=4))
```
## `pagination_items`

`pagination_items` is a function that allows to get current pagination items. It can be useful when you need to get
current items in a specific context. Here is an example of how it can be used:

```py
from __future__ import annotations
from typing import TypeVar, Generic, Sequence, Optional, Any

from fastapi import FastAPI
from fastapi_pagination import Params, add_pagination, paginate
from fastapi_pagination.bases import AbstractParams, AbstractPage
from fastapi_pagination.api import pagination_items

from pydantic import BaseModel, Field

T = TypeVar("T")


class InnerModel(BaseModel, Generic[T]):
    results: list[T] = Field(default_factory=pagination_items)


class MyPageResponse(AbstractPage[T]):
    inner: InnerModel[T]

    __params_type__ = Params

    @classmethod
    def create(
        cls,
        items: Sequence[T],
        params: AbstractParams,
        *,
        total: Optional[int] = None,
        **kwargs: Any,
    ) -> MyPageResponse[T]:
        return cls(inner={})

app = FastAPI()
add_pagination(app)

# req: GET /nums?page=2&size=10
@app.get("/nums")
async def route() -> MyPageResponse[int]:
    return paginate([*range(100)])
```


## `set_params`

`set_params` is a function that allows to set current pagination params.
It also can be used as a context manager to set params for a specific context.

```py
from fastapi_pagination import Params
from fastapi_pagination.api import set_params

# set global params
set_params(Params(page=2, size=10))

# set params for a specific context
with set_params(Params(page=3, size=20)):
    pass
```

## `resolve_params`

`resolve_params` is a function that allows to get current pagination params.
In case if `set_params` was called before, then `resolve_params` will return the same params as `set_params` was called with.
If `resolve_params` was called with param `params` argument, then this argument will be returned.

```py
from fastapi_pagination import Params
from fastapi_pagination.api import resolve_params, set_params

set_params(Params(page=2, size=10))

print(resolve_params())

with set_params(Params(page=3, size=20)):
    print(resolve_params())

print(resolve_params(Params(page=4, size=30)))
```

## `set_items_transformer`

`set_items_transformer` is a function that allows to set a transformer for items. It works similar to how 
`set_params` function works.

```py
from fastapi_pagination.api import set_items_transformer

set_items_transformer(lambda items: [x * 2 for x in items])

with set_items_transformer(lambda items: [x * 3 for x in items]):
    pass
```

## `resolve_items_transformer`

`resolve_items_transformer` is a function that allows to get current items transformer.
It works similar to how `resolve_params` function works.

```py
from dataclasses import dataclass
from fastapi_pagination.api import resolve_items_transformer, set_items_transformer


@dataclass
class Transformer:
    name: str
    multiplier: int

    def __call__(self, items: list[int]) -> list[int]:
        return [x * self.multiplier for x in items]

set_items_transformer(Transformer("double", 2))
print(resolve_items_transformer())

with set_items_transformer(Transformer("triple", 3)):
    print(resolve_items_transformer())

print(resolve_items_transformer(Transformer("quadruple", 4)))
```

## `apply_items_transformer`

`apply_items_transformer` is a function that allows to apply items transformer to items. It can be used for 
sync and async items transformation.

Sync items transformation:
```py
from fastapi_pagination.api import (
    set_items_transformer,
    apply_items_transformer,
)

set_items_transformer(lambda items: [x * 2 for x in items])
r1 = apply_items_transformer([1, 2, 3])
print(f"{r1=}")

r2 = apply_items_transformer(
    [1, 2, 3],
    transformer=lambda items: [x * 3 for x in items],
)
print(f"{r2=}")
```


Async items transformation:
```py
from fastapi_pagination.api import (
    set_items_transformer,
    apply_items_transformer,
)

async def transformer_double(items: list[int]) -> list[int]:
    return [x * 2 for x in items]

set_items_transformer(transformer_double)
r1 = await apply_items_transformer([1, 2, 3], async_=True)
print(f"{r1=}")

async def transformer_triple(items: list[int]) -> list[int]:
    return [x * 3 for x in items]

r2 = await apply_items_transformer(
    [1, 2, 3],
    transformer=transformer_triple,
    async_=True,
)
print(f"{r2=}")
```

## `response`/`request`

`response` and `request` are functions that allow to get current response and request objects.
It can be useful when you need to add information some information to `response` or get information about `request`.

```py
from fastapi import FastAPI
from fastapi_pagination import Page, add_pagination, paginate
from fastapi_pagination.api import response, request

app = FastAPI()
add_pagination(app)


# req: GET /nums?page=2&size=10
@app.get("/nums")
async def get_nums() -> Page[int]:
    print({**request().headers})
    response().status_code = 201

    return paginate(range(100))
```

