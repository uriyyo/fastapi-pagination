from asyncio import get_event_loop

from nest_asyncio import apply
from pytest import fixture


def pytest_addoption(parser):
    parser.addoption(
        "--postgres-dsn",
        type=str,
        required=True,
    )


@fixture(scope="session")
def postgres_url(request) -> str:
    return request.config.getoption("--postgres-dsn")


@fixture(scope="session")
def sqlite_url() -> str:
    return "sqlite:///.db"


@fixture(
    scope="session",
    params=["postgres_url", "sqlite_url"],
)
def database_url(request) -> str:
    return request.getfixturevalue(request.param)


@fixture(scope="session")
def event_loop():
    apply()
    return get_event_loop()
