from asyncio import new_event_loop

from pytest import fixture


def pytest_addoption(parser):
    parser.addoption(
        "--postgres-dsn",
        type=str,
        required=True,
    )
    parser.addoption(
        "--mongodb-dsn",
        type=str,
        required=True,
    )


@fixture(scope="session")
def postgres_url(request) -> str:
    return request.config.getoption("--postgres-dsn")


@fixture(scope="session")
def mongodb_url(request) -> str:
    return request.config.getoption("--mongodb-dsn")


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
    return new_event_loop()
