`UseOptionalParams` is a customizer that allows to make your `Params` class fields optional.
It will allow you to be able to select all available items in case if some of input parameters are not provided.

```py
from typing import TypeVar

from fastapi import FastAPI
from fastapi_pagination import Page, add_pagination, paginate
from fastapi_pagination.customization import CustomizedPage, UseOptionalParams

app = FastAPI()
add_pagination(app)

T = TypeVar("T")

CustomPage = CustomizedPage[
    Page[T],
    UseOptionalParams()
]

# req: GET /nums?size=5&page=1
# req: GET /nums
@app.get("/nums")
async def get_nums() -> CustomPage[int]:
    return paginate(range(100))
```
