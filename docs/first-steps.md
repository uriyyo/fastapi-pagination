It's pretty easy to use `fastapi-pagination`.

First, you need to import `Page`, `Params` and one of `paginate`
functions from `fastapi_pagination`.

* `Page` - is used as `response_model` in your route declaration.
* `Params` - is a user provide params for pagination.
* `paginate` - is a function that will paginate your data.

```python
from fastapi_pagination import Page, Params, paginate
from fastapi import Depends, FastAPI
from pydantic import BaseModel


class User(BaseModel):
    name: str


app = FastAPI()

users = [
    User(name="Yurii"),
    # ...
]


@app.get(
    "/",
    response_model=Page[User],
)
def route(params: Params = Depends()):
    return paginate(users, params)
```

In case when you don't like to explicitly pass `params` you can use
`add_pagination` function and use params implicitly.

```python
from fastapi_pagination import Page, paginate, add_pagination
from fastapi import FastAPI
from pydantic import BaseModel


class User(BaseModel):
    name: str


app = FastAPI()

users = [
    User(name="Yurii"),
    # ...
]


@app.get(
    "/",
    response_model=Page[User],
)
async def route():
    return paginate(users)


add_pagination(app)
```
