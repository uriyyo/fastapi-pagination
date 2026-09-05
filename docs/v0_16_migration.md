# Breaking Changes in v0.16

## 1. `pydantic` v1 support was dropped

`pydantic` package now requires version `2.13.4` or higher.

`UsePydanticV1` customization and all version specific helpers from `fastapi_pagination.pydantic`
were removed.

## 2. Deprecated async `paginate` functions were removed

Async `paginate` functions, that were deprecated in `v0.15.0`, are now removed.
Please use `apaginate` instead.

```python
# before
from fastapi_pagination.ext.sqlalchemy import paginate

# after
from fastapi_pagination.ext.sqlalchemy import apaginate
```

## 3. Deprecated extensions were removed

`motor`, `odmantic`, `bunnet`, `databases`, `orm`, `gino` and `pony` extensions were removed,
together with their extras.

Please use `fastapi_pagination.ext.pymongo` instead of `motor`/`odmantic`/`bunnet`
and `fastapi_pagination.ext.sqlalchemy` instead of `databases`/`orm`/`gino`.

## 4. Min versions update

`fastapi` package now requires version `0.140.13` or higher, `piccolo` - `1.0` or higher.

`elasticsearch` extra now installs `elasticsearch>=8.18.0` instead of `elasticsearch-dsl`.
