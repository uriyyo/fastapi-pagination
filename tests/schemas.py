from pydantic import BaseModel

from fastapi_pagination.pydantic import IS_PYDANTIC_V2
from fastapi_pagination.pydantic.v1 import BaseModelV1


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


class BaseSchemaV1(BaseModelV1):
    class Config:
        orm_mode = True


class OrderOutV1(BaseSchemaV1):
    id: int
    name: str


class UserOutV1(BaseSchemaV1):
    id: int
    name: str


class UserWithoutIDOutV1(BaseSchemaV1):
    name: str


class UserWithOrderOutV1(BaseSchemaV1):
    id: int
    name: str

    orders: list[OrderOutV1]


__all__ = [
    "OrderOut",
    "OrderOutV1",
    "UserOut",
    "UserOutV1",
    "UserWithOrderOut",
    "UserWithOrderOutV1",
    "UserWithoutIDOut",
    "UserWithoutIDOutV1",
]
