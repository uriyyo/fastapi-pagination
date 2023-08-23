# SQLAlchemy

A minimal example of using the SQLAlchemy integration can be seen below:

```python
from sqlalchemy import select
from fastapi_pagination.ext.sqlalchemy import paginate


@app.get('/users', response_model=Page[UserOut])
def get_users(db: Session = Depends(get_db)):
    return paginate(db, select(User).order_by(User.created_at))
```

## Scalar column

If you want to paginate a scalar column and return non-scalar value, then you will need to use `transformer`
```python
from sqlalchemy import select
from fastapi_pagination.ext.sqlalchemy import paginate
from pydantic import BaseModel


class UserNameOut(BaseModel):
    name: str

    
@app.get('/users', response_model=Page[UserNameOut])
def get_user_names(db: Session = Depends(get_db)):
    return paginate(
        db,
        select(User.name).order_by(User.created_at),
        transformer=lambda items: [{"name": name} for name in items],
    )
```