import asyncio
from functools import lru_cache

from pydantic import generics

# https://github.com/pydantic/pydantic/issues/4483
generics._generic_types_cache = {}
generics._assigned_parameters = {}


@lru_cache()
def _get_event_loop_no_warn(*_):
    loop = asyncio.new_event_loop()
    loop.__pytest_asyncio = True

    return loop


# plugin._get_event_loop_no_warn = _get_event_loop_no_warn
