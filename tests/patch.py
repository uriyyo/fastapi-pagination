import sys
import warnings

from fastapi_pagination.pydantic import IS_PYDANTIC_V2

if sys.version_info[:2] == (3, 10):
    warnings.filterwarnings(
        "ignore",
        message="You are using a Python version.*google.api_core",
        category=FutureWarning,
    )

if not IS_PYDANTIC_V2:
    from pydantic import generics

    # https://github.com/pydantic/pydantic/issues/4483
    generics._generic_types_cache = {}
    generics._assigned_parameters = {}
