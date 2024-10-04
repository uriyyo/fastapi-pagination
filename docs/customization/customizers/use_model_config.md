`UseModelConfig` is a customizer that allows you to change `pydantic` model configuration for a `Page` class.

```py
from typing import TypeVar

from fastapi import FastAPI
from fastapi_pagination import Page, add_pagination, paginate
from fastapi_pagination.customization import CustomizedPage, UseModelConfig

from string import ascii_lowercase

app = FastAPI()
add_pagination(app)

T = TypeVar("T")

CustomPage = CustomizedPage[
    Page[T],
    UseModelConfig(
        str_to_upper=True,
    ),
]

# req: GET /nums?pageSize=5&pageNumber=2
@app.get("/nums")
async def get_nums() -> CustomPage[str]:
    return paginate([*ascii_lowercase])
```