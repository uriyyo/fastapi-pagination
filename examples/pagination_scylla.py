import uuid
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from cassandra.cluster import Cluster
from cassandra.cqlengine import columns, connection, management, models
from faker import Faker
from fastapi import FastAPI
from pydantic import BaseModel

from fastapi_pagination import add_pagination
from fastapi_pagination.cursor import CursorPage as BaseCursorPage
from fastapi_pagination.ext.cassandra import paginate

faker = Faker()

CursorPage = BaseCursorPage.with_custom_options(str_cursor=False)


class User(models.Model):
    __keyspace__ = "ks"

    id = columns.UUID(primary_key=True)
    name = columns.Text()
    email = columns.Text()


class UserIn(BaseModel):
    name: str
    email: str


class UserOut(UserIn):
    id: int

    class Config:
        orm_mode = True


@asynccontextmanager
async def lifespan(_: Any) -> None:
    ddl = "CREATE KEYSPACE IF NOT EXISTS ks WITH replication = {'class': 'SimpleStrategy', 'replication_factor': '1'}"
    session.execute(ddl)
    connection.register_connection("cluster1", session=session, default=True)
    management.sync_table(model=User, keyspaces=("ks",))

    users = [User(id=uuid.uuid4(), name=faker.name(), email=faker.email()) for _ in range(100)]
    for user in users:
        user.save()
    yield


app = FastAPI(lifespan=lifespan)
session = Cluster(
    [
        "172.17.0.2",
    ]
).connect()


@app.post("/users", response_model=UserOut)
def create_user(user_in: UserIn) -> User:
    user = User(id=uuid.uuid4(), name=user_in.name, email=user_in.email)
    user.save()
    return user


@app.get("/users/cursor", response_model=CursorPage[UserOut])
def get_users() -> Any:
    return paginate(User)


add_pagination(app)

if __name__ == "__main__":
    uvicorn.run("pagination_scylla:app")
