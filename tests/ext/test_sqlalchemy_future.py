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

from ..base import BasePaginationTestCase, UserOut
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
def app(Base, User, SessionLocal):
    app = FastAPI()

    @app.on_event("startup")
    def on_startup():
        Base.metadata.create_all()

        with SessionLocal() as session:
            session.add_all([User(name=faker.name()) for _ in range(100)])

    def get_db() -> Iterator[Session]:
        with SessionLocal() as db:
            yield db

    @app.get("/default", response_model=Page[UserOut])
    @app.get("/limit-offset", response_model=LimitOffsetPage[UserOut])
    def route(db: Session = Depends(get_db)):
        return paginate(db, select(User))

    add_pagination(app)
    return app


@mark.future_sqlalchemy
class TestSQLAlchemyFuture(BasePaginationTestCase):
    @fixture(scope="session")
    def entities(self, SessionLocal, User):
        with SessionLocal() as session:
            return session.execute(select(User)).unique().scalars().all()
