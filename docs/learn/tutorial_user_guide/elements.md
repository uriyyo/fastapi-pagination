# General

`fastapi-pagination` provide a set of elements that can be used to implement pagination in your FastAPI application.
These elements are designed to be flexible and easy to use, allowing you to customize the pagination behavior to suit your needs.

`fastapi-pagination` provides implementation of different pagination techniques, such as `limit-offset`, `page-based`, and `cursor-based` pagination.

By `default` `fastapi-pagination` refers to `page-based` pagination, but you can easily switch to other
pagination techniques by importing the corresponding from corresponding module.

* `fastapi_pagination.default` - `page-based` pagination
* `fastapi_pagination.limit_offset` - `limit-offset` pagination
* `fastapi_pagination.cursor` - `cursor-based` pagination

# Params

`Params` is a class that represents the pagination parameters. It describes input parameters for pagination,
such as `limit` and `offset` for `limit-offset` pagination, or `page` and `size` for `page-based` pagination.

Here is an example of available `Params` classes:
```python
from fastapi_pagination.default import Params
from fastapi_pagination.cursor import CursorParams
from fastapi_pagination.limit_offset import LimitOffsetParams
```

Vanilla `Params` class for `page-based` pagination will look like this:
```python
from pydantic import BaseModel
from fastapi import Query

class Params(BaseModel):
    page: int = Query(1, ge=1)
    size: int = Query(50, ge=1, le=100)
```

# Page

`Page` is a class that represents a single page of paginated data. It contains the data for the current page,
as well as metadata such as the total number of items and the number of items per page.

Here is an example of available `Page` classes:
```python
from fastapi_pagination.default import Page
from fastapi_pagination.cursor import CursorPage
from fastapi_pagination.limit_offset import LimitOffsetPage
```

# Paginate

`paginate` is a function that takes a query, pagination parameters, and a function to execute the query.
It returns a `Page` object containing the paginated data.

`paginate` function is used to integrate `fastapi-pagination` with different ORMs and databases.

!!! warning

    Default `fastapi_pagination.paginate` function is used to paginate the data that already exists in memory.
    If you are working with a database or an ORM, you should use `paginate` function from `ext` module of the corresponding ORM.
    For example, `sqlalchemy` ORM provides `paginate` method for pagination. In case if there is no `paginate` function
    available for the ORM you are using, you can implement it by yourself.
