from pydantic import BaseModel

from fastapi_pagination.utils import IS_PYDANTIC_V2


class BaseSchema(BaseModel):
    if IS_PYDANTIC_V2:
        model_config = {
            "from_attributes": True,
        }
    else:

        class Config:
            orm_mode = True


class OrderOut(BaseSchema):
    id: int
    name: str


class UserOut(BaseSchema):
    id: int
    name: str


class UserWithoutIDOut(BaseSchema):
    name: str


class UserWithOrderOut(BaseSchema):
    id: int
    name: str

    orders: list[OrderOut]


__all__ = [
    "OrderOut",
    "UserOut",
    "UserWithOrderOut",
    "UserWithoutIDOut",
]
