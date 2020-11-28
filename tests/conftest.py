from asyncio import get_event_loop

from nest_asyncio import apply
from pytest import fixture


@fixture(scope="session")
def event_loop():
    apply()
    return get_event_loop()
