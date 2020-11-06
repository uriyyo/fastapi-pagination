# FastAPI Pagination

## Installation

Basic version
```bash
pip install fastapi-pagination
```

`Gino` integration
```bash
pip install fastapi-pagination[gino]
```

`SQLAlchemy` integration
```bash
pip install fastapi-pagination[sqlalchemy]
```

## Example

```python
from fastapi import FastAPI, Depends
from pydantic import BaseModel

from fastapi_pagination import PaginationParams, Page
from fastapi_pagination.paginator import paginate

app = FastAPI()

class User(BaseModel):
    name: str
    surname: str

users = [
    User(name='Yurii', surname='Karabas'),
    # ...
]

@app.get('/users', response_model=Page[User])
async def get_users(params: PaginationParams = Depends()):
    return paginate(users, params)
```
