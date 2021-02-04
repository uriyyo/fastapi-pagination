To use `limit-offset` pagination you should set
`fastapi_pagination.limit_offset.Page` as page model using `fastapi_pagination.using_page`
function.

```python
from fastapi_pagination.limit_offset import Page
from fastapi_pagination import using_page

using_page(Page)
```

After that `fastapi_pagination.limit_offset.Page` and
`fastapi_pagination.limit_offset.pagination_params` should be used at route declaration.

```python
from fastapi_pagination.limit_offset import Page, pagination_params


@router.get(
    '',
    response_model=Page[User],
    dependencies=[Depends(pagination_params)],
)
async def route():
    ...
```

Fully working example can be
found [here](https://github.com/uriyyo/fastapi-pagination/tree/main/examples/pagination_limit_offset.py).