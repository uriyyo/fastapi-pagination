Here is an example:

```py
from fastapi import FastAPI
from fastapi_pagination import Page, add_pagination, paginate

app = FastAPI()
add_pagination(app)


# req: GET /users?page=2&size=10
@app.get("/users")
async def get_users() -> Page[int]:
    return paginate([*range(100)])
```

Steps:

1. Import `Page`, `add_pagination`, and `paginate` from `fastapi_pagination`.
2. Create a `FastAPI` application instance.
3. Add pagination support to the `FastAPI` application using `add_pagination`.
4. Define a route handler that returns a paginated response `Page[int]`.
5. Use the `paginate` function to paginate the data and return the paginated response.


!!! warning

    The `paginate` function is used to paginate the data that already exists in memory.
    If you are working with a database or an ORM, you should use the appropriate methods provided by
    the database or ORM to paginate the data.

The example above will be equal to the following vanilla FastAPI code:

```py
from fastapi import FastAPI, Depends
from fastapi_pagination import Page, Params, paginate, set_page

app = FastAPI()

# req: GET /users?page=2&size=10
@app.get("/users")
async def get_users(params: Params = Depends()) -> Page[int]:
    set_page(Page[int])

    return paginate([*range(100)], params)
```
