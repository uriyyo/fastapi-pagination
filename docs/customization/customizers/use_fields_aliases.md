`UseFieldAliases` allows you to change default names of fields in a `Page` class when it is serialized.

```py
from typing import TypeVar

from fastapi import FastAPI
from fastapi_pagination import Page, add_pagination, paginate
from fastapi_pagination.customization import CustomizedPage, UseFieldsAliases

app = FastAPI()
add_pagination(app)

T = TypeVar("T")

CustomPage = CustomizedPage[
    Page[T],
    UseFieldsAliases(
        items="content",
        size="pageSize",
        page="pageNumber",
        pages="totalPages",
        total="totalElements",
    ),
]

# req: GET /nums?size=5&page=2
@app.get("/nums")
async def get_nums() -> CustomPage[int]:
    return paginate(range(1_000))
```