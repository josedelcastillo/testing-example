"""Fixtures de integración: PostgreSQL real.

Estrategia de aislamiento: cada prueba corre dentro de una transacción
que se revierte al final. Las pruebas no se contaminan entre sí y no hace
falta limpiar tablas manualmente.
"""

import os
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.db import DEFAULT_URL, get_session
from app.main import app, get_payment_gateway
from app.models import Base
from app.payments import FakePaymentGateway
from app.repository import SqlRepository

pytestmark = pytest.mark.integration


@pytest.fixture(scope="session")
def engine():
    url = os.getenv("DATABASE_URL", DEFAULT_URL)
    engine = create_engine(url)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except OperationalError as exc:
        pytest.fail(
            f"No hay conexión a PostgreSQL ({url}).\n"
            "Levántalo con: docker compose up -d db\n"
            f"Detalle: {exc.orig}",
            pytrace=False,
        )
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def session(engine):
    connection = engine.connect()
    outer = connection.begin()
    # "create_savepoint": los commit() del código bajo prueba solo liberan un
    # SAVEPOINT; la transacción externa se revierte al terminar la prueba.
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    yield session
    session.close()
    outer.rollback()
    connection.close()


@pytest.fixture
def repository(session):
    return SqlRepository(session)


@pytest.fixture
def gateway():
    return FakePaymentGateway(limit=Decimal("1000.00"))


@pytest.fixture
def client(session, gateway):
    """Cliente HTTP que usa la sesión transaccional de la prueba."""
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[get_payment_gateway] = lambda: gateway
    # Sin "with": no se dispara el lifespan, el esquema ya lo creó `engine`.
    yield TestClient(app)
    app.dependency_overrides.clear()
