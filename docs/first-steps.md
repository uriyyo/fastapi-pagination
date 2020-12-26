It's pretty easy to use `fastapi-pagination`.

First, you need to import `Page`, `PaginationParams` and one of `paginate`
functions from `fastapi_pagination`.

* `Page` - is used as `response_model` in your route declaration.
* `PaginationParams` - is a user provide params for pagination.
* `paginate` - is a function that will paginate your data.

```python
from fastapi_pagination import Page, PaginationParams, paginate
from fastapi import FastAPI
from pydantic import BaseModel


class User(BaseModel):
    name: str


app = FastAPI()
users = [User("Yurii"), ...]


@app.get(
    "/",
    response_model=Page[User],
)
def route(params: PaginationParams):
    return paginate(users, params)
```

In case when you don't like to explicitly pass `params` you can use
`fastapi` dependency and use params implicitly.

```python
from fastapi_pagination import pagination_params


@app.get(
    "/",
    response_model=Page[User],
    dependencies=[Depends(pagination_params)]
)
def route():
    return paginate(users)
```