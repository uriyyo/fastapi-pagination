`fastapi-pagination` provides a way to customize your input and output models.

In most cases you will find needed customizer is `fastapi_pagination.customization` module.

`CustomizedPage` works similar to how `typing.Annotated` works, but as arguments it accepts instances of 
`PageCustomizer` protocol.

Here is an examples of how to increase default size of params:
```py
from typing import TypeVar

from fastapi import FastAPI, Query
from fastapi_pagination import Page, paginate, add_pagination
from fastapi_pagination.customization import CustomizedPage, UseParamsFields

app = FastAPI()
add_pagination(app)

T = TypeVar("T")

CustomPage = CustomizedPage[
    Page[T],
    UseParamsFields(
        size=Query(100, ge=1, le=1000),
    ),
]

# req: GET /nums
@app.get("/nums")
async def get_nums() -> CustomPage[int]:
    return paginate(range(1_000))
```
