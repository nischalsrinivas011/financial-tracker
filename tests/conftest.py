from dotenv import load_dotenv

load_dotenv()

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models import Base
from app.db.session import engine
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def _schema():
    Base.metadata.create_all(engine)


@pytest.fixture
def db_session():
    """A DB session bound to a transaction that's rolled back after the
    test, so nothing persists in the shared real Neon database (project
    decision: no local SQLite stand-in). create_savepoint: a test that
    triggers an intentional IntegrityError still leaves this fixture's own
    rollback with a live transaction to close cleanly.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    """A FastAPI TestClient whose DB dependency is overridden to use the
    rollback-wrapped db_session fixture, so API tests hit the same
    isolated transaction as direct-model tests.
    """
    app.dependency_overrides[get_db] = lambda: db_session
    yield TestClient(app)
    app.dependency_overrides.clear()
