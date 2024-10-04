`UseExcludeFields` allows you to exclude some fields from the `Page` class.

Here is an example of how you remove `size`, `page`, `pages` and `total` fields from the `Page` class:

```py
from typing import TypeVar

from fastapi import FastAPI
from fastapi_pagination import Page, add_pagination, paginate
from fastapi_pagination.customization import CustomizedPage, UseExcludedFields

app = FastAPI()
add_pagination(app)

T = TypeVar("T")

CustomPage = CustomizedPage[
    Page[T],
    UseExcludedFields("size", "page", "pages", "total"),
]

# req: GET /nums?size=5&page=2
@app.get("/nums")
async def get_nums() -> CustomPage[int]:
    return paginate(range(1_000))
```
