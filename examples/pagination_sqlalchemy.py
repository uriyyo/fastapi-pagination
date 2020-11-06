import uvicorn
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from fastapi_pagination import Page, PaginationParams
from fastapi_pagination.ext.sqlalchemy import paginate

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


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/users", response_model=UserOut)
def create_user(user_in: UserIn, db: Session = Depends(get_db)):
    user = User(name=user_in.name, email=user_in.email)
    db.add(user)
    db.flush()

    return user


@app.get("/users", response_model=Page[UserOut])
def get_users(db: Session = Depends(get_db), params: PaginationParams = Depends()):
    return paginate(db.query(User), params)


if __name__ == "__main__":
    uvicorn.run("pagination_sqlalchemy:app")
