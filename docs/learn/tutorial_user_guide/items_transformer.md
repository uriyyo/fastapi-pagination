## Items Transformer

The items transformer allows to transform the items before they are returned in the response.
This can be useful for formatting the data or adding additional information to the items.

It's a class that accepts a chunk of items and returns a new chunk of items that will be used in the response.

```py
from fastapi import FastAPI
from fastapi_pagination import Page, add_pagination, paginate

app = FastAPI()
add_pagination(app)

# req: GET /ints?page=2&size=5
@app.get("/ints")
async def route() -> Page[int]:
    return paginate(
        range(100),
        transformer=lambda items: [item * 2 for item in items],  # double the items
    )
```

Items transformer can be also set globally:

```py
from fastapi import FastAPI
from fastapi_pagination import Page, add_pagination, paginate
from fastapi_pagination.api import set_items_transformer

app = FastAPI()
add_pagination(app)

set_items_transformer(lambda items: [item * 2 for item in items])

# req: GET /ints?page=2&size=5
@app.get("/ints")
async def route() -> Page[int]:
    return paginate(range(100))


# req: GET /another-ints?page=2&size=5
@app.get("/another-ints")
async def another_route() -> Page[int]:
    return paginate(range(100))
```

Or per route:

```py
from fastapi import FastAPI
from fastapi_pagination import Page, add_pagination, paginate
from fastapi_pagination.api import set_items_transformer

app = FastAPI()
add_pagination(app)

# req: GET /ints?page=2&size=5
@app.get("/ints")
async def route() -> Page[int]:
    set_items_transformer(lambda items: [item * 2 for item in items])
    return paginate(range(100))

# req: GET /ints-no-transformer?page=2&size=5
@app.get("/ints-no-transformer")
async def another_route() -> Page[int]:
    return paginate(range(100))
```

If `paginate` function is async, then the transformer can be async too:

```py
from fastapi import FastAPI
from fastapi_pagination import Page, add_pagination
from fastapi_pagination.async_paginator import paginate

app = FastAPI()
add_pagination(app)

async def transformer(items: list[int]) -> list[int]:
    return [item * 2 for item in items]

# req: GET /ints?page=2&size=5
@app.get("/ints")
async def route() -> Page[int]:
    return await paginate(range(100), transformer=transformer)
```
