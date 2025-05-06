import pytest
import json
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from bdi_api.settings import Settings

# Mock settings
class TestSettings(Settings):
    DB_HOST: str = 'aircraft-db'
    DB_PORT: str = '5432'
    DB_USER: str = 'postgres'
    DB_PASSWORD: str = 'postgres'
    DB_NAME: str = 'test_aircraft_db'
    AWS_ACCESS_KEY_ID: str = 'test'
    AWS_SECRET_ACCESS_KEY: str = 'test'
    AWS_REGION: str = 'us-east-1'
    S3_BUCKET: str = 'test-bucket'

    class Config:
        env_file = None

# Create test settings instance
test_settings = TestSettings()

# Patch settings before importing app
with patch('bdi_api.settings.settings', test_settings):
    from bdi_api.s7.api import app, get_db, Base

@pytest.fixture
def test_db():
    # Test database fixture
    engine = create_engine(
        f"postgresql://{test_settings.DB_USER}:{test_settings.DB_PASSWORD}@{test_settings.DB_HOST}:{test_settings.DB_PORT}/{test_settings.DB_NAME}"
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(engine)

@pytest.fixture
def mock_s3():
    # S3 mock fixture
    mock_s3 = MagicMock()
    mock_s3.list_objects_v2.return_value = {
        'Contents': [
            {'Key': 'test.json'}
        ]
    }
    mock_s3.get_object.return_value = {
        'Body': MagicMock(
            read=lambda: json.dumps([{
                'icao': 'A320',
                'altitude': 30000,
                'speed': 500
            }])
        )
    }
    with patch('boto3.client', return_value=mock_s3):
        yield mock_s3
