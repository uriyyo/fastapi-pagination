import pytest
from dirty_equals import IsStr
from fastapi import FastAPI, status
from starlette.testclient import TestClient

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.links import LimitOffsetPage as LinksLimitOffsetPage
from fastapi_pagination.links import Page as LinksPage
from fastapi_pagination.optional import OptionalLimitOffsetPage, OptionalPage
from fastapi_pagination.pydantic import IS_PYDANTIC_V2

app = FastAPI()
add_pagination(app)

client = TestClient(app)


CASES = [
    ("default", Page[int]),
    ("limit-offset", LimitOffsetPage[int]),
    ("links-default", LinksPage[int]),
    ("links-limit-offset", LinksLimitOffsetPage[int]),
    ("optional-default", OptionalPage[int]),
    ("optional-limit-offset", OptionalLimitOffsetPage[int]),
]

for name, page in CASES:

    @app.get(f"/{name}", response_model=page)
    async def route():
        pass


@pytest.mark.skipif(
    not IS_PYDANTIC_V2,
    reason="We don't check OpenAPI schema for Pydantic v1, as support for it will be dropped in the future.",
)
@pytest.mark.parametrize(
    ("endpoint", "schema"),
    [
        (
            "/default",
            {
                "properties": {
                    "items": {"items": {"type": "integer"}, "title": "Items", "type": "array"},
                    "page": {"minimum": 1.0, "title": "Page", "type": "integer"},
                    "pages": {"minimum": 0.0, "title": "Pages", "type": "integer"},
                    "size": {"minimum": 1.0, "title": "Size", "type": "integer"},
                    "total": {"minimum": 0.0, "title": "Total", "type": "integer"},
                },
                "required": ["items", "total", "page", "size", "pages"],
                "title": IsStr,
                "type": "object",
            },
        ),
        (
            "/limit-offset",
            {
                "properties": {
                    "items": {"items": {"type": "integer"}, "title": "Items", "type": "array"},
                    "limit": {"minimum": 1.0, "title": "Limit", "type": "integer"},
                    "offset": {"minimum": 0.0, "title": "Offset", "type": "integer"},
                    "total": {"minimum": 0.0, "title": "Total", "type": "integer"},
                },
                "required": ["items", "total", "limit", "offset"],
                "title": IsStr,
                "type": "object",
            },
        ),
        (
            "/links-default",
            {
                "properties": {
                    "items": {"items": {"type": "integer"}, "type": "array", "title": "Items"},
                    "total": {"type": "integer", "minimum": 0.0, "title": "Total"},
                    "page": {"type": "integer", "minimum": 1.0, "title": "Page"},
                    "size": {"type": "integer", "minimum": 1.0, "title": "Size"},
                    "pages": {"type": "integer", "minimum": 0.0, "title": "Pages"},
                    "links": {"$ref": "#/components/schemas/Links", "readOnly": True},
                },
                "type": "object",
                "required": ["items", "total", "page", "size", "pages", "links"],
                "title": IsStr,
            },
        ),
        (
            "/links-limit-offset",
            {
                "properties": {
                    "items": {"items": {"type": "integer"}, "type": "array", "title": "Items"},
                    "total": {"type": "integer", "minimum": 0.0, "title": "Total"},
                    "limit": {"type": "integer", "minimum": 1.0, "title": "Limit"},
                    "offset": {"type": "integer", "minimum": 0.0, "title": "Offset"},
                    "links": {"$ref": "#/components/schemas/Links", "readOnly": True},
                },
                "type": "object",
                "required": ["items", "total", "limit", "offset", "links"],
                "title": IsStr,
            },
        ),
        (
            "/optional-default",
            {
                "properties": {
                    "items": {"items": {"type": "integer"}, "type": "array", "title": "Items"},
                    "total": {"anyOf": [{"type": "integer", "minimum": 0.0}, {"type": "null"}], "title": "Total"},
                    "page": {"anyOf": [{"type": "integer", "minimum": 1.0}, {"type": "null"}], "title": "Page"},
                    "size": {"anyOf": [{"type": "integer", "minimum": 1.0}, {"type": "null"}], "title": "Size"},
                    "pages": {"anyOf": [{"type": "integer", "minimum": 0.0}, {"type": "null"}], "title": "Pages"},
                },
                "type": "object",
                "required": ["items"],
                "title": IsStr,
            },
        ),
        (
            "/optional-limit-offset",
            {
                "properties": {
                    "items": {"items": {"type": "integer"}, "type": "array", "title": "Items"},
                    "total": {"anyOf": [{"type": "integer", "minimum": 0.0}, {"type": "null"}], "title": "Total"},
                    "limit": {"anyOf": [{"type": "integer", "minimum": 1.0}, {"type": "null"}], "title": "Limit"},
                    "offset": {"anyOf": [{"type": "integer", "minimum": 0.0}, {"type": "null"}], "title": "Offset"},
                },
                "type": "object",
                "required": ["items"],
                "title": IsStr,
            },
        ),
    ],
)
def test_openapi_schema(endpoint, schema):
    response = client.get("/openapi.json")
    assert response.status_code == status.HTTP_200_OK

    openapi_schema = response.json()

    endpoint = openapi_schema["paths"][endpoint]
    schema_ref = endpoint["get"]["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]
    *_, name = schema_ref.split("/")
    actual_schema = openapi_schema["components"]["schemas"][name]

    assert actual_schema == schema
