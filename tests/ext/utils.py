from pytest import fixture, mark

try:
    from sqlalchemy import __version__ as sqlalchemy_version

    is_sqlalchemy20 = tuple(map(int, sqlalchemy_version.split("."))) >= (2, 0, 0)

    del sqlalchemy_version
except (ImportError, AttributeError):
    is_sqlalchemy20 = False

sqlalchemy20 = mark.sqlalchemy20

only_sqlalchemy20 = mark.skipif(
    lambda: not is_sqlalchemy20,
    reason="Only for SQLAlchemy 2.0",
)


class _MongoDBTestCase:
    @fixture(scope="session")
    def database_url(self, mongodb_url):
        return mongodb_url

    @fixture(scope="session")
    def db_type(self):
        return "mongodb"


def mongodb_test(cls):
    assert isinstance(cls, type), "mongodb_test can only be used with classes"

    new_cls = type(cls.__name__, (_MongoDBTestCase, cls), {})
    return mark.mongodb(new_cls)
