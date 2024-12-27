from pathlib import Path
from typing import Any, Union

import pytest
from sqlalchemy import Column, ForeignKey, Integer, String, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, relationship, sessionmaker
from typing_extensions import TypeAlias

try:
    from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
    from sqlalchemy.orm import declarative_base
except ImportError:
    create_async_engine = None
    AsyncSession = None
    AsyncEngine = None

    from sqlalchemy.ext.declarative import declarative_base

try:
    from sqlmodel import Field, Relationship, SQLModel
except ImportError:
    SQLModel = None
    Field = None
    Relationship = None

PossiblyAsyncEngine: TypeAlias = Union[Engine, AsyncEngine]


@pytest.fixture(scope="session")
def sa_engine_params(database_url: str) -> dict:
    return {}


@pytest.fixture(scope="session")
def sa_engine(database_url: str, sa_engine_params: dict, is_async_db: bool) -> PossiblyAsyncEngine:
    if is_async_db:
        return create_async_engine(database_url, **sa_engine_params)

    return create_engine(database_url, **sa_engine_params)


@pytest.fixture(scope="session")
def sa_session(sa_engine: PossiblyAsyncEngine, is_async_db: bool):
    session_cls = AsyncSession if is_async_db else Session
    return sessionmaker(bind=sa_engine, class_=session_cls)


@pytest.fixture(scope="session")
def sa_base(sa_engine: PossiblyAsyncEngine):
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
def sm_user(sm_order):
    class User(SQLModel, table=True):
        __tablename__ = "users"

        id: int = Field(primary_key=True)
        name: str

        orders: list[sm_order] = Relationship()

    return User


@pytest.fixture(scope="session")
def sm_order():
    class Order(SQLModel, table=True):
        __tablename__ = "orders"

        id: int = Field(primary_key=True)
        user_id: int = Field(foreign_key="users.id")
        name: str

    return Order


@pytest.fixture(scope="session")
def sm_session_ctx(sa_session, is_async_db):
    if is_async_db:

        async def ctx():
            async with sa_session() as session:
                yield session
    else:

        def ctx():
            with sa_session() as session:
                yield session

    return ctx


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
    if module.endswith(".py"):
        module = module[:-3]

    try:
        __import__(f"tests.ext.{module}")
    except (ImportError, ModuleNotFoundError):
        return DummyModule.from_parent(parent, name=module, path=path, nodeid=module)
