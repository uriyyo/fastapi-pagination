from fastapi import FastAPI

from fastapi_pagination import Page, add_pagination, paginate

app = FastAPI()
add_pagination(app)


@app.get("/double-nums")
def get_double_nums() -> Page[int]:
    return paginate(
        [*range(1_000)],
        transformer=lambda x: [i * 2 for i in x],
    )
