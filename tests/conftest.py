import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from bdi_api.s7.api import Base, AircraftStats

TEST_DATABASE_URL = "postgresql://postgres:postgres@aircraft-db:5432/test_aircraft_db"

@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def test_db(test_engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()
