from datetime import date
from pathlib import Path
from typing import Any, Iterator, Dict, TypeVar

from faker import Faker
from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Field, Session, SQLModel, create_engine, select

from fastapi_pagination import pagination_ctx, resolve_params
from fastapi_pagination.cursor import CursorPage as BaseCursorPage
from fastapi_pagination.customization import CustomizedPage, UseIncludeTotal, UseParamsFields
from fastapi_pagination.ext.sqlmodel import paginate

ROOT = Path(__file__).parent

fake = Faker()

app = FastAPI()
templates = Jinja2Templates(directory=ROOT / "templates")

engine = create_engine("sqlite:///.db")


T = TypeVar("T")

CursorPage = CustomizedPage[
    BaseCursorPage[T],
    UseIncludeTotal(True),
    UseParamsFields(size=10),
]


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int = Field(primary_key=True)
    profile_pic: str
    first_name: str
    last_name: str
    email: str
    created_at: date


def get_db() -> Iterator[Session]:
    with Session(engine) as session:
        yield session


def user_data(id_: int) -> Dict[str, Any]:
    return {
        "id": id_ + 1,
        "profile_pic": f"https://api.dicebear.com/8.x/croodles/svg?seed={id_ + 1}",
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": fake.email(),
        "created_at": fake.date_between("-3y"),
    }


@app.on_event("startup")
def on_startup():
    User.metadata.drop_all(engine)
    User.metadata.create_all(engine)

    total = fake.pyint(100, 200)

    with Session(engine) as session:
        session.add_all([User(**user_data(i)) for i in range(total)])
        session.commit()


@app.get(
    "/",
    response_class=HTMLResponse,
    dependencies=[Depends(pagination_ctx(CursorPage[User]))],
)
def get_page(
    request: Request,
    db: Session = Depends(get_db),
) -> Any:
    page = paginate(db, select(User).order_by(User.created_at, User.id))

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "page": page,
            "params": resolve_params(),
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app)
