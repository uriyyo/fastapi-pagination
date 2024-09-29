When you want to add metadata with information about `first/last/next/previous` pages, you can use pages
from `fastapi_pagination.links` module.

```py
from fastapi import FastAPI
from fastapi_pagination import add_pagination, paginate
from fastapi_pagination.links import Page

app = FastAPI()
add_pagination(app)

# req: GET /nums?page=2&size=10
@app.get("/nums")
async def get_users() -> Page[int]:
    return paginate(range(200))
```

Also, there is limit-offset page with links:

```py
from fastapi import FastAPI
from fastapi_pagination import add_pagination, paginate
from fastapi_pagination.links import LimitOffsetPage

app = FastAPI()
add_pagination(app)

# req: GET /nums?offset=10&limit=5
@app.get("/nums")
async def get_users() -> LimitOffsetPage[int]:
    return paginate(range(200))
```
