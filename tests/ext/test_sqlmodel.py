from functools import partial
from typing import Iterator

from fastapi import Depends, FastAPI
from pytest import fixture, mark
from sqlmodel import Field, Session, SQLModel, create_engine, select

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.sqlmodel import paginate

from ..base import BasePaginationTestCase, UserOut
from ..utils import faker


@fixture(scope="session")
def engine(database_url):
    if database_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    else:
        connect_args = {}

    return create_engine(database_url, connect_args=connect_args)


@fixture(scope="session")
def SessionLocal(engine):
    return partial(Session, engine)


@fixture(scope="session")
def User():
    class User(SQLModel, table=True):
        id: int = Field(primary_key=True)
        name: str

    return User


@fixture(
    scope="session",
    params=[True, False],
    ids=["model", "query"],
)
def query(request, User):
    if request.param:
        return User
    else:
        return select(User)


@fixture(scope="session")
def app(query, engine, User, SessionLocal):
    app = FastAPI()

    @app.on_event("startup")
    def on_startup():
        SQLModel.metadata.create_all(engine)

        with SessionLocal() as session:
            session.add_all([User(name=faker.name()) for _ in range(100)])

    def get_db() -> Iterator[Session]:
        with SessionLocal() as db:
            yield db

    @app.get("/default", response_model=Page[UserOut])
    @app.get("/limit-offset", response_model=LimitOffsetPage[UserOut])
    def route(db: Session = Depends(get_db)):
        return paginate(db, query)

    add_pagination(app)
    return app


@mark.future_sqlalchemy
class TestSQLModel(BasePaginationTestCase):
    @fixture(scope="session")
    def entities(self, SessionLocal, User):
        with SessionLocal() as session:
            return session.exec(select(User)).unique().all()
