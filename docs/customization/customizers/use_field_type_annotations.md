`UseFieldTypeAnnotations` allows you to update type annotations of the fields in the `Page` class.

```py
from typing import TypeVar

from fastapi import FastAPI
from fastapi_pagination import Page, add_pagination, paginate
from fastapi_pagination.customization import CustomizedPage, UseFieldTypeAnnotations

app = FastAPI()
add_pagination(app)

T = TypeVar("T")

CustomPage = CustomizedPage[
    Page[T],
    UseFieldTypeAnnotations(
        total=float,  # change type of `total` field to `float`
    )
]

# req: GET /nums?size=5&page=2
@app.get("/nums")
async def get_nums() -> CustomPage[int]:
    return paginate(range(1_000))
```
