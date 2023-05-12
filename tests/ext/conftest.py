from typing import List

from pytest import fixture
from sqlalchemy import Column, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import Session, relationship, sessionmaker

try:
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import declarative_base
except ImportError:
    create_async_engine = None
    AsyncSession = None

    from sqlalchemy.ext.declarative import declarative_base

try:
    from sqlmodel import Field, Relationship, SQLModel
except ImportError:
    SQLModel = None
    Field = None
    Relationship = None


@fixture(scope="session")
def sa_engine_params(database_url):
    return {}


@fixture(scope="session")
def sa_engine(database_url, sa_engine_params, is_async_db):
    if is_async_db:
        return create_async_engine(database_url, **sa_engine_params)

    return create_engine(database_url, **sa_engine_params)


@fixture(scope="session")
def sa_session(sa_engine, is_async_db):
    session_cls = AsyncSession if is_async_db else Session
    return sessionmaker(bind=sa_engine, class_=session_cls)


@fixture(scope="session")
def sa_base(sa_engine):
    return declarative_base()


@fixture(scope="session")
def sa_order(sa_base):
    class Order(sa_base):
        __tablename__ = "orders"

        id = Column(Integer, primary_key=True)
        user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
        name = Column(String)

        user = relationship("User", back_populates="orders")

    return Order


@fixture(scope="session")
def sa_user(sa_base, sa_order):
    class User(sa_base):
        __tablename__ = "users"

        id = Column(Integer, primary_key=True, autoincrement=True)
        name = Column(String, nullable=False)

        orders = relationship("Order", back_populates="user", lazy="noload")

    return User


@fixture(scope="session")
def sm_user(sm_order):
    class User(SQLModel, table=True):
        __tablename__ = "users"

        id: int = Field(primary_key=True)
        name: str

        orders: List[sm_order] = Relationship()

    return User


@fixture(scope="session")
def sm_order():
    class Order(SQLModel, table=True):
        __tablename__ = "orders"

        id: int = Field(primary_key=True)
        user_id: int = Field(foreign_key="users.id")
        name: str

    return Order
