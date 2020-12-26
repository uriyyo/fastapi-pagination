There are 3 thing you should know about:

* `Page` - `pydantic` model that represents paginated results.
* `PaginationParams` - class that represents pagination params passed from user.
* `paginate` - function that is used to paginate your query and data.

## `Page` and `PaginationParams`

`fastapi-pagination` by default provides you with 2 implementations of `Page` and `PaginationParams`.

### 1. `Page` and `PaginationParams` (default)

`PaginationParams` constrains:

1. `page` >= 0
2. 0 < `size` <= 100 (default value 50)

Data schema of `PaginationParams`:

```json
{
  "page": 0,
  "size": 50
}
```

Data schema of `Page`:

```json
{
  "items": [
    ...
  ],
  "page": 0,
  "size": 50,
  "total": 100
}
```

Can be imported from `fastapi_pagination`.

### 2. Limit-Offset `Page` and `PaginationParams`

`PaginationParams` constrains:

1. 0 < `limit` <= 100 (default value 50)
2. `offset` > 0

Data schema of `PaginationParams`:

```json
{
  "offset": 0,
  "limit": 50
}
```

Data schema of `Page`:

```json
{
  "items": [
    ...
  ],
  "page": 0,
  "offset": 0,
  "limit": 50
}
```

Can be imported from `fastapi_pagination.limi_offset`.

## `paginate`

`paginate` - it is function that paginate your query or data.

`fastapi_pagination.paginate` - can be used to paginate any python sequence like tuple or list

```python
from fastapi_pagination import paginate

users = [...]


@app.get("/", response_model=Page[UserOut])
async def route(params: Params):
    return paginate(users, params)
```

All integrations with existing libraries are located in `fastapi_pagination.ext` package.

To see fully working integrations usage, please visit this
[link](https://github.com/uriyyo/fastapi-pagination/tree/main/examples).

