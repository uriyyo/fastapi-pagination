import sys

import pytest

from tests.base import SuiteBuilder
from tests.schemas import UserWithoutIDOut

try:
    from sqlalchemy import __version__ as sqlalchemy_version

    is_sqlalchemy20 = tuple(map(int, sqlalchemy_version.split("."))) >= (2, 0, 0)

    del sqlalchemy_version
except (ImportError, AttributeError):
    is_sqlalchemy20 = False

sqlalchemy20 = pytest.mark.sqlalchemy20

only_sqlalchemy20 = pytest.mark.skipif(
    lambda: not is_sqlalchemy20,
    reason="Only for SQLAlchemy 2.0",
)

skip_python_314 = pytest.mark.skipif(
    sys.version_info[:2] == (3, 14),
    reason="Skip tests on Python 3.14 due to incompatibilities",
)


class _MongoDBTestCase:
    @pytest.fixture(scope="session")
    def db_type(self):
        return "mongodb"

    @pytest.fixture(scope="session")
    def database_url(self, mongodb_url):
        return mongodb_url

    @classmethod
    def create_builder(cls) -> SuiteBuilder:
        return SuiteBuilder().with_classes(
            model=UserWithoutIDOut,
        )


def mongodb_test(cls):
    assert isinstance(cls, type), "mongodb_test can only be used with classes"

    new_cls = type(cls.__name__, (_MongoDBTestCase, cls), {})
    return pytest.mark.mongodb(new_cls)
