from random import randint
from typing import Iterator

from fastapi import Depends, FastAPI
from pytest import fixture, mark
from sqlalchemy import Column, ForeignKey, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.future import select
from sqlalchemy.orm import relationship, selectinload, sessionmaker
from sqlalchemy.orm.session import Session

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.sqlalchemy_future import paginate

from ..base import BasePaginationTestCase
from ..utils import faker


@fixture(scope="session")
def engine(database_url):
    return create_engine(database_url)


@fixture(scope="session")
def SessionLocal(engine):
    return sessionmaker(autocommit=True, autoflush=True, bind=engine)


@fixture(scope="session")
def Base(engine):
    return declarative_base(bind=engine)


@fixture(scope="session")
def Order(Base):
    class Order(Base):  # noqa
        __tablename__ = "orders"

        id = Column(Integer, primary_key=True)
        user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
        name = Column(String)

        user = relationship("User", back_populates="orders")

    return Order


@fixture(scope="session")
def User(Base, Order):
    class User(Base):
        __tablename__ = "users"

        id = Column(Integer, primary_key=True, autoincrement=True)
        name = Column(String, nullable=False)

        orders = relationship("Order", back_populates="user", lazy="noload")

    return User


@fixture(scope="session")
def app(Base, User, SessionLocal, model_cls, model_with_rel_cls):
    app = FastAPI()

    def get_db() -> Iterator[Session]:
        with SessionLocal() as db:
            yield db

    @app.get("/default", response_model=Page[model_cls])
    @app.get("/limit-offset", response_model=LimitOffsetPage[model_cls])
    def route(db: Session = Depends(get_db)):
        return paginate(db, select(User))

    @app.get("/relationship/default", response_model=Page[model_with_rel_cls])
    @app.get("/relationship/limit-offset", response_model=LimitOffsetPage[model_with_rel_cls])
    def route(db: Session = Depends(get_db)):
        return paginate(db, select(User).options(selectinload(User.orders)))

    @app.get("/non-scalar/default", response_model=Page[model_cls])
    @app.get("/non-scalar/limit-offset", response_model=LimitOffsetPage[model_cls])
    def route_non_scalar(db: Session = Depends(get_db)):
        return paginate(db, select(User.id, User.name))

    return add_pagination(app)


@mark.future_sqlalchemy
class TestSQLAlchemyFuture(BasePaginationTestCase):
    @fixture(scope="class")
    def entities(self, SessionLocal, User, Order):
        with SessionLocal() as session:
            session.add_all(
                [
                    User(
                        name=faker.name(),
                        orders=[Order(name=faker.name()) for _ in range(randint(0, 10))],
                    )
                    for _ in range(100)
                ]
            )

            return session.execute(select(User).options(selectinload(User.orders))).unique().scalars().all()


@mark.future_sqlalchemy
class TestSQLAlchemyFutureNonScalar(TestSQLAlchemyFuture):
    page_path = "/non-scalar/default"
    limit_offset_page_path = "/non-scalar/limit-offset"


@mark.future_sqlalchemy
class TestSQLAlchemyFutureRelationship(TestSQLAlchemyFuture):
    page_path = "/relationship/default"
    limit_offset_page_path = "/relationship/limit-offset"

    @fixture(scope="session")
    def model_cls(self, model_with_rel_cls):
        return model_with_rel_cls
