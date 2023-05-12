from pytest import mark

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
