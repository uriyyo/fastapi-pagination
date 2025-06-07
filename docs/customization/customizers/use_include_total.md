`UseIncludeTotal` allows you to control whether the total number should be calculated or not.

For instance, `CursorPage` by default don't calculate the total number of items, but you can change this
behavior by using `UseIncludeTotal` customizer.

```py
from typing import TypeVar, Any

from fastapi import FastAPI
from fastapi_pagination import Page, paginate, add_pagination
from fastapi_pagination.customization import CustomizedPage, UseIncludeTotal

app = FastAPI()
add_pagination(app)

T = TypeVar("T")

PageNoTotal = CustomizedPage[
    Page[T],
    UseIncludeTotal(False),
]
PageWithTotal = CustomizedPage[
    Page[T],
    UseIncludeTotal(True),
]

# req: GET /nums-no-total?size=5
@app.get("/nums-no-total", response_model=PageNoTotal[int])
# req: GET /nums-with-total?size=5
@app.get("/nums-with-total", response_model=PageWithTotal[int])
async def get_nums() -> Any:
    return paginate(range(1_000))
```


By default `UseIncludeTotal` will update type annotation of `total` field to be optional in case if `include_total` is set to `False`,
or it will be required if `include_total` is set to `True`. You can override this behavior by passing `update_annotations` argument to `UseIncludeTotal`.

```py
from typing import TypeVar

from fastapi_pagination import Page
from fastapi_pagination.customization import CustomizedPage, UseIncludeTotal

T = TypeVar("T")

PageWithTotal = CustomizedPage[
    Page[T],
    UseIncludeTotal(
        True,
        update_annotations=False,
    ),
]
```
