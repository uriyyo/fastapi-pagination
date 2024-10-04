## How can I change default size of page params?

To change default size of page params, you can use `CustomizedPage` and `UseParamsFields` customizer:

```py
from typing import TypeVar

from fastapi import FastAPI, Query
from fastapi_pagination import Page, add_pagination, paginate
from fastapi_pagination.customization import CustomizedPage, UseParamsFields

app = FastAPI()
add_pagination(app)

T = TypeVar("T")

CustomPage = CustomizedPage[
    Page[T],
    UseParamsFields(
        # change default size to be 5, increase upper limit to 1 000
        size=Query(5, ge=1, le=1_000),
    ),
]


# req: GET /nums
@app.get("/nums")
async def get_nums() -> CustomPage[int]:
    return paginate(range(1_000))
```

## I'm getting `RuntimeError` error in my tests, what should I do?

If you are getting `RuntimeError: Use params, add_pagination or pagination_ctx and had no clue about what should I do.`,
the easiest way to fix it is to add call `set_params` function in your test:

```python
from fastapi_pagination import set_params, Params

def test_my_endpoint():
    set_params(Params(size=10, page=2))
    # your test code
```

But better solution will be to make sure that `lifespan` was called on app that you are testing:

```python
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import AsyncClient
from pytest_asyncio import fixture


@fixture
async def client(app: FastAPI):
    async with AsyncClient(app=app, base_url="http://test") as app_client:
        async with LifespanManager(app):
            yield app_client
```
