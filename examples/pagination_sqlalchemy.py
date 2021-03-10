from typing import Any, Iterator

import uvicorn
from faker import Faker
from fastapi import Depends, FastAPI
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.sqlalchemy import paginate

faker = Faker()

engine = create_engine("sqlite:///.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=True, autoflush=True, bind=engine)

Base = declarative_base(bind=engine)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)


Base.metadata.drop_all()
Base.metadata.create_all()


class UserIn(BaseModel):
    name: str
    email: str


class UserOut(UserIn):
    id: int

    class Config:
        orm_mode = True


app = FastAPI()


@app.on_event("startup")
def on_startup() -> None:
    session = SessionLocal()

    session.add_all([User(name=faker.name(), email=faker.email()) for _ in range(100)])

    session.flush()
    session.close()


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/users", response_model=UserOut)
def create_user(user_in: UserIn, db: Session = Depends(get_db)) -> User:
    user = User(name=user_in.name, email=user_in.email)
    db.add(user)
    db.flush()

    return user


@app.get("/users/default", response_model=Page[UserOut])
@app.get("/users/limit-offset", response_model=LimitOffsetPage[UserOut])
def get_users(db: Session = Depends(get_db)) -> Any:
    return paginate(db.query(User))


add_pagination(app)

if __name__ == "__main__":
    uvicorn.run("pagination_sqlalchemy:app")
