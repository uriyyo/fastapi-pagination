from functools import partial
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import Column, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import Session, relationship

from tests.utils import create_ctx

try:
    from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
    from sqlalchemy.orm import declarative_base
except ImportError:
    create_async_engine = None
    AsyncSession = None
    AsyncEngine = None

    from sqlalchemy.ext.declarative import declarative_base


@pytest.fixture(scope="session")
def sa_engine(database_url: str, is_async_db: bool):
    if is_async_db:
        from sqlalchemy.ext.asyncio import create_async_engine

        return create_async_engine(database_url)

    return create_engine(database_url)


@pytest.fixture(scope="session")
def sa_session(sa_engine, is_async_db: bool):
    return partial(AsyncSession if is_async_db else Session, sa_engine)


@pytest.fixture(scope="session")
def sa_base(sa_engine):
    return declarative_base()


@pytest.fixture(scope="session")
def sa_order(sa_base):
    class Order(sa_base):
        __tablename__ = "orders"

        id = Column(Integer, primary_key=True)
        user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
        name = Column(String)

        user = relationship("User", back_populates="orders")

    return Order


@pytest.fixture(scope="session")
def sa_user(sa_base, sa_order):
    class User(sa_base):
        __tablename__ = "users"

        id = Column(Integer, primary_key=True, autoincrement=True)
        name = Column(String, nullable=False)

        orders = relationship("Order", back_populates="user", lazy="noload")

    return User


@pytest.fixture(scope="session")
def sa_session_ctx(sa_session, is_async_db):
    return create_ctx(sa_session, is_async_db)


class _SkipExtItem(pytest.Item):
    def setup(self) -> None:
        pass

    def runtest(self) -> Any:
        pass


class DummyModule(pytest.Module):
    def collect(self):
        # return skipped item here
        return []

    def _getobj(self):
        return __import__("tests.ext.test_dummy")


ROOT = Path(__file__).parent
DUMMY = ROOT / "test_dummy.py"


def pytest_pycollect_makemodule(module_path, path, parent):
    if not module_path.name.startswith("test_"):
        return None

    p = module_path.relative_to(ROOT)
    module = ".".join(p.parts)
    module = module.removesuffix(".py")

    try:
        __import__(f"tests.ext.{module}")
    except (ImportError, ModuleNotFoundError):
        return DummyModule.from_parent(parent, name=module, path=path, nodeid=module)
