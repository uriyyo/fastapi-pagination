## Default

By default, if you are using the `add_pagination` function, then the only thing you need to do is to use the
`response_model` or set the return type annotation to be a subclass of `AbstractPage`.


```py
from fastapi import FastAPI
from fastapi_pagination import Page, add_pagination, paginate

app = FastAPI()
add_pagination(app)


# req: GET /return-type-ann?page=2&size=5
@app.get("/return-type-ann")
async def route() -> Page[int]:
    return paginate(range(100))

# req: GET /return-model?page=2&size=5
@app.get("/return-model", response_model=Page[int])
async def route():
    return paginate(range(100))
```


## Non-Page response model

If you want to return a non-Page response model, you can use the `set_page` function to set the response model, but
then you will need to explicitly specify the params value in the route handler.

```py
from typing import Annotated

from fastapi import FastAPI, Depends
from fastapi_pagination import Params, Page, paginate, set_page

app = FastAPI()


# req: GET /non-page?page=2&size=5
@app.get("/non-page")
async def route(params: Annotated[Params, Depends()]) -> list[int]:
    set_page(Page[int])
    page = paginate(range(100), params=params)
    return page.items
```

## Multiple Page response models for a single route handler

If you want to return multiple Page response models for a single route handler, you can use the `response_model` parameter
in the route declaration.

```py
from typing import Any

from fastapi import FastAPI
from fastapi_pagination import Page, LimitOffsetPage, add_pagination, paginate

app = FastAPI()
add_pagination(app)

# req: GET /page?page=2&size=5
@app.get("/page", response_model=Page[int])
# req: GET /limit-offset?limit=5&offset=5
@app.get("/limit-offset", response_model=LimitOffsetPage[int])
async def route() -> Any:
    return paginate(range(100))
```
