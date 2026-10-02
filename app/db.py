import os
from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

DEFAULT_URL = "postgresql+psycopg://tienda:tienda@localhost:5432/tienda"


@lru_cache
def get_engine() -> Engine:
    return create_engine(os.getenv("DATABASE_URL", DEFAULT_URL), pool_pre_ping=True)


def get_session() -> Iterator[Session]:
    with Session(get_engine()) as session:
        yield session
