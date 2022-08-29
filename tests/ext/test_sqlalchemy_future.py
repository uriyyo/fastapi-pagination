from typing import Iterator

from fastapi import Depends, FastAPI
from pytest import fixture, mark
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker
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
def User(Base):
    class User(Base):
        __tablename__ = "users"

        id = Column(Integer, primary_key=True, autoincrement=True)
        name = Column(String, nullable=False)

    return User


@fixture(scope="session")
def app(Base, User, SessionLocal, model_cls):
    app = FastAPI()

    def get_db() -> Iterator[Session]:
        with SessionLocal() as db:
            yield db

    @app.get("/default", response_model=Page[model_cls])
    @app.get("/limit-offset", response_model=LimitOffsetPage[model_cls])
    def route(db: Session = Depends(get_db)):
        return paginate(db, select(User))

    @app.get("/non-scalar/default", response_model=Page[model_cls])
    @app.get("/non-scalar/limit-offset", response_model=LimitOffsetPage[model_cls])
    def route_non_scalar(db: Session = Depends(get_db)):
        return paginate(db, select(User.id, User.name))

    return add_pagination(app)


@mark.future_sqlalchemy
class TestSQLAlchemyFuture(BasePaginationTestCase):
    @fixture(scope="class")
    def entities(self, SessionLocal, User):
        with SessionLocal() as session:
            session.add_all([User(name=faker.name()) for _ in range(100)])

            return session.execute(select(User)).unique().scalars().all()


@mark.future_sqlalchemy
class TestSQLAlchemyFutureNonScalar(TestSQLAlchemyFuture):
    page_path = "/non-scalar/default"
    limit_offset_page_path = "/non-scalar/limit-offset"
