Currently, `fastapi-pagination` supports:

| Library                                                                | `paginate` function                            | 
|------------------------------------------------------------------------|------------------------------------------------|
| [SQLAlchemy](https://docs.sqlalchemy.org/en/14/orm/quickstart.html)    | `fastapi_pagination.ext.sqlalchemy.paginate`   |
| [SQLModel](https://sqlmodel.tiangolo.com/)                             | `fastapi_pagination.ext.sqlmodel.paginate`     |
| [Peewee](https://docs.peewee-orm.com/)                                 | `fastapi_pagination.ext.peewee.paginate`       |
| [AsyncPG](https://magicstack.github.io/asyncpg/current/)               | `fastapi_pagination.ext.asyncpg.apaginate`     |
| [Django ORM](https://docs.djangoproject.com/en/3.2/topics/db/queries/) | `fastapi_pagination.ext.django.paginate`       |
| [ormar](https://collerek.github.io/ormar/)                             | `fastapi_pagination.ext.ormar.apaginate`       |
| [Piccolo](https://piccolo-orm.readthedocs.io/en/latest/)               | `fastapi_pagination.ext.piccolo.apaginate`     |
| [Tortoise ORM](https://tortoise.github.io/)                            | `fastapi_pagination.ext.tortoise.apaginate`    |
| [Beanie](https://roman-right.github.io/beanie/)                        | `fastapi_pagination.ext.beanie.apaginate`      |
| [PyMongo](https://pymongo.readthedocs.io/en/stable/)                   | `fastapi_pagination.ext.pymongo.paginate`      |
| [MongoEngine](https://docs.mongoengine.org/)                           | `fastapi_pagination.ext.mongoengine.paginate`  |
| [Cassandra](https://python-driver.docs.scylladb.com/stable/)           | `fastapi_pagination.ext.cassandra.paginate`    |
| [Psycopg](https://www.psycopg.org/psycopg3/docs/)                      | `fastapi_pagination.ext.psycopg.paginate`      |
