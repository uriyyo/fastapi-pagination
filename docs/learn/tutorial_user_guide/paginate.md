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

## Async `paginate` function

If you want to use async `paginate` function, you can use `fastapi_pagination.async_paginator` module.
It exists to be able to use async `transformer` function.

```py
from fastapi import FastAPI
from fastapi_pagination import add_pagination, Page
from fastapi_pagination.async_paginator import paginate

app = FastAPI()
add_pagination(app)

# req: GET /nums?page=2&size=10
@app.get("/nums")
async def get_users() -> Page[int]:
    return await paginate(range(200))
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
