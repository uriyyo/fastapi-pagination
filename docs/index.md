# FastAPI Pagination

FastAPI Pagination - easy to use pagination for FastAPI.

## Installation

```bash
pip install fastapi-pagination
```

To install fastapi-pagination with all available integrations:

```bash
pip install fastapi-pagination[all]
```

## Minimal Example

Example of code and generated OpenAPI specification.

```python
from fastapi import FastAPI
from pydantic import BaseModel

from fastapi_pagination import Page, add_pagination, paginate

app = FastAPI()


class User(BaseModel):
    name: str
    surname: str


users = [
    User(name='Yurii', surname='Karabas'),
    # ...
]


@app.get('/users', response_model=Page[User])
async def get_users():
    return paginate(users)


add_pagination(app)
```

![OpenAPI](img/openapi_example.png)
