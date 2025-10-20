# Contributing

Any and all contributions and involvement with the project is welcome. The easiest way to begin contributing is to check out the open issues on GitHub.

## Documentation

The documentation is built using [mkdocs](https://www.mkdocs.org/). All documentation is in markdown format, and can be found in `./docs/`


## Contributing Code

### Step 1: prerequisites

`fastapi-pagination` uses [uv](https://docs.astral.sh/uv/) for dependency management.
Please, install uv before continuing.

Minimum supported python version is `3.10`.


### Step 2: clone the repo

```shell
git clone https://github.com/uriyyo/fastapi-pagination
```


### Step 3: install dependencies

To install all dependencies, run:
```sh
uv sync --dev --all-extras
```

To install only basic dependencies, run:
```sh
uv install --dev
```

To install docs requirements, run:
```sh
uv pip install -r docs_requirements.txt
```

### Step 4: do your changes

If you want to add new feature, please, create an issue first and describe your idea.

If you want to add new extension for pagination you will need to create a new module in `fastapi_pagination/ext/` directory.
Please, use `fastapi_pagination/ext/sqlalchemy.py` as an example.
Generally, you will need to call function `paginate` and signature should include next arguments:
```py
from typing import Any, Optional

from fastapi_pagination.api import apply_items_transformer, create_page
from fastapi_pagination.bases import AbstractParams
from fastapi_pagination.types import AdditionalData, AsyncItemsTransformer
from fastapi_pagination.utils import verify_params


async def paginate(
    query: Any,
    params: Optional[AbstractParams] = None,  # Optional params for pagination (if None, current params will be used)
    *,
    transformer: Optional[AsyncItemsTransformer] = None,  # Optional transformer for items
    additional_data: Optional[AdditionalData] = None,  # Optional additional data for page object
) -> Any:
    params, raw_params = verify_params(params, "limit-offset")  # verify params is of correct type

    total = await query.count()  # get total count of items
    items = await query.limit(raw_params.limit).offset(raw_params.offset).all()  # get items for current page
    t_items = await apply_items_transformer(items, transformer, async_=True)  # apply transformer if needed

    return create_page(  # create page object
        t_items,
        total=total,
        params=params,
        **(additional_data or {}),
    )
```

If you want to add/updated docs, then you will need to edit `./docs/` directory.
You can run `mkdocs serve` to see your changes locally.

### Step 5: run pre-commit hooks

Before creating a commit, please, run pre-commit hooks:
```sh
uv run pre-commit run --all-files
```

You can also install pre-commit hooks to run automatically before each commit:
```sh
uv run pre-commit install
```

### Step 6: run tests

Before running tests, you need to prepare env:
```sh
./scripts/ci-prepare.sh
```

To run tests, run:
```sh
uv run pytest tests
```

If you want to run tests with coverage, run:
```sh
uv run pytest tests --cov=fastapi_pagination
```

If you want to run only unit tests, run:
```sh
uv run pytest tests --unit-tests
```

If you want to run only integration tests, then you will also will need to have `PostgreSQL`, `MongoDB` and `Casandra` running.

To run integration tests, run:
```sh
uv run pytest tests/ext
```

If you want to run whole test suite, run:
```sh
./scripts/ci-test.sh
```

### Step 7: create a pull request

After you have done all changes, please, create a pull request.