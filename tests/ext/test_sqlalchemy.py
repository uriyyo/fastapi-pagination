from typing import Iterator

from fastapi import Depends, FastAPI
from pytest import fixture
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.sqlalchemy import paginate

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
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    @app.get("/default", response_model=Page[model_cls])
    @app.get("/limit-offset", response_model=LimitOffsetPage[model_cls])
    def route(db: Session = Depends(get_db)):
        return paginate(db.query(User))

    return add_pagination(app)


class TestSQLAlchemy(BasePaginationTestCase):
    @fixture(scope="class")
    def entities(self, SessionLocal, User):
        session = SessionLocal()
        try:
            session.add_all([User(name=faker.name()) for _ in range(100)])

            return session.query(User).all()
        finally:
            session.close()
