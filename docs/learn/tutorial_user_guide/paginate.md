`paginate` is a default name for a function that used to paginate data, but you can use any name you want :smile:.

`fastapi-pagination` provides several pagination function that can be used to `paginate` data that is
already in memory.

## Default `paginate` function

The default `paginate` function is used to paginate the data that is already in memory.

```py
from fastapi import FastAPI
from fastapi_pagination import add_pagination, paginate, Page

app = FastAPI()
add_pagination(app)

# req: GET /nums?page=2&size=10
@app.get("/nums")
async def get_users() -> Page[int]:
    return paginate(range(200))
```

## `additional_data`

You can pass extra keyword arguments to the page model with `additional_data`.
This is useful when your page type defines custom fields, for example with `UseAdditionalFields`.

```py
from fastapi import FastAPI
from fastapi_pagination import add_pagination, paginate, Page
from fastapi_pagination.customization import CustomizedPage, UseAdditionalFields

app = FastAPI()
add_pagination(app)

CustomPage = CustomizedPage[
    Page[int],
    UseAdditionalFields(page_sum=int),
]


@app.get("/nums")
async def get_users() -> CustomPage[int]:
    return paginate(
        range(200),
        additional_data=lambda items: {"page_sum": sum(items)},
    )
```

For sync `paginate`, `additional_data` can be either:

* a dictionary
* a sync callable that receives the current page items and returns a dictionary

For `fastapi_pagination.async_paginator.apaginate`, `additional_data` can also be an async callable.

## Async `apaginate` function

If you want to use async pagination, you can use `apaginate` from the `fastapi_pagination.async_paginator` module.
It exists to be able to use async `transformer` function.

```py
from fastapi import FastAPI
from fastapi_pagination import add_pagination, Page
from fastapi_pagination.async_paginator import apaginate

app = FastAPI()
add_pagination(app)

# req: GET /nums?page=2&size=10
@app.get("/nums")
async def get_users() -> Page[int]:
    return await apaginate(range(200))
```

Async `apaginate` also supports async `additional_data` callbacks:

```py
from fastapi_pagination.async_paginator import apaginate


async def get_page_data(items: list[int]) -> dict[str, int]:
    return {"page_sum": sum(items)}


@app.get("/nums/async")
async def get_async_users() -> CustomPage[int]:
    return await apaginate(
        range(200),
        additional_data=get_page_data,
    )
```

## Iterable `paginate` function

If you have iterable generator, and you want to paginate it, you can use `paginate`
from `fastapi_pagination.iterables` function.

```py
from typing import Iterable

from fastapi import FastAPI
from fastapi_pagination import add_pagination, Page
from fastapi_pagination.iterables import paginate

app = FastAPI()
add_pagination(app)

def nums() -> Iterable[int]:
    for i in range(200):
        yield i


# req: GET /nums?page=2&size=10
@app.get("/nums")
async def get_users() -> Page[int]:
    return paginate(nums())
```
