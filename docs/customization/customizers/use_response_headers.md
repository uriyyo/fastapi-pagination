`UseResponseHeaders` allows to add custom headers to the response based on page instance.

```py
from typing import TypeVar

from fastapi import FastAPI, Query
from fastapi_pagination import Page, add_pagination, paginate
from fastapi_pagination.customization import CustomizedPage, UseResponseHeaders

app = FastAPI()
add_pagination(app)

T = TypeVar("T")

CustomPage = CustomizedPage[
    Page[T],
    UseResponseHeaders(
        lambda page: {
            "X-Total-Items": str(page.total),
            "X-Total-Pages": str(page.pages),
        },
    ),
]


# req(+headers): GET /nums?page=2&size=5
@app.get("/nums")
async def get_nums() -> CustomPage[int]:
    return paginate(range(1_000))
```