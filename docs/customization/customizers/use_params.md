`UseParams` allows you to change `Params` class for a `Page`.

```py
from typing import TypeVar

from fastapi import FastAPI, Query
from fastapi_pagination import Page, Params, add_pagination, paginate
from fastapi_pagination.customization import CustomizedPage, UseParams

app = FastAPI()
add_pagination(app)

T = TypeVar("T")

class MyParams(Params):
    size: int = Query(20, ge=1, le=100, alias="pageSize")
    page: int = Query(1, ge=1, alias="pageNumber")


CustomPage = CustomizedPage[
    Page[T],
    UseParams(MyParams),
]

# req: GET /nums?pageSize=5&pageNumber=2
@app.get("/nums")
async def get_nums() -> CustomPage[int]:
    return paginate(range(1_000))
```
