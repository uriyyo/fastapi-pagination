import sqlalchemy
from databases import Database
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from orm import Integer, Model, String
from pytest import fixture

from fastapi_pagination import (
    LimitOffsetPage,
    LimitOffsetPaginationParams,
    Page,
    PaginationParams,
)
from fastapi_pagination.ext.orm import paginate

from ..base import (
    BasePaginationTestCase,
    UserOut,
    limit_offset_params,
    page_params,
)
from ..utils import faker

metadata = sqlalchemy.MetaData()
db = Database("sqlite:///.db")


class User(Model):
    __tablename__ = "users"
    __database__ = db
    __metadata__ = metadata

    id = Integer(primary_key=True)
    name = String(max_length=100)


app = FastAPI()


@app.on_event("startup")
async def on_startup() -> None:
    engine = sqlalchemy.create_engine(str(db.url))
    metadata.drop_all(engine)
    metadata.create_all(engine)

    await db.connect()

    for _ in range(100):
        await User.objects.create(name=faker.name())


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await db.disconnect()


@app.get("/implicit", response_model=Page[UserOut], dependencies=[Depends(page_params)])
async def route():
    return await paginate(User.objects)


@app.get("/explicit", response_model=Page[UserOut])
async def route(params: PaginationParams = Depends()):
    return await paginate(User.objects, params)


@app.get(
    "/implicit-limit-offset",
    response_model=LimitOffsetPage[UserOut],
    dependencies=[Depends(limit_offset_params)],
)
async def route():
    return await paginate(User.objects)


@app.get("/explicit-limit-offset", response_model=LimitOffsetPage[UserOut])
async def route(params: LimitOffsetPaginationParams = Depends()):
    return await paginate(User.objects, params)


class TestORM(BasePaginationTestCase):
    @fixture(scope="session")
    async def client(self):
        with TestClient(app) as c:
            yield c

    @fixture(scope="session")
    async def entities(self):
        return await User.objects.all()
