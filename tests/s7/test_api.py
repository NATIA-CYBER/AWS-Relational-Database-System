import pytest
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from botocore.exceptions import ClientError
from bdi_api.settings import Settings

# Test-specific settings
class TestSettings(Settings):
    DB_HOST: str = 'db'
    DB_PORT: str = '5432'
    DB_USER: str = 'postgres'
    DB_PASSWORD: str = 'postgres'
    DB_NAME: str = 'test_aircraft_db'
    AWS_ACCESS_KEY_ID: str = 'test'
    AWS_SECRET_ACCESS_KEY: str = 'test'
    AWS_REGION: str = 'us-east-1'
    S3_BUCKET: str = 'test-bucket'

    model_config = {
        'env_file': None
    }  # Disable .env file loading in tests

test_settings = TestSettings()

# Patch settings before importing app
with patch('bdi_api.settings.settings', test_settings):
    from bdi_api.settings import engine, SessionLocal
    from bdi_api.s7.api import app, get_db, get_s3_client, Base, AircraftStats

# Keep settings patched during tests
@pytest.fixture(autouse=True)
def patch_settings():
    with patch('bdi_api.settings.settings', test_settings):
        yield

@pytest.fixture(autouse=True)
def setup_database():
    # Drop all tables first to ensure clean state
    Base.metadata.drop_all(bind=engine)
    # Create all tables
    Base.metadata.create_all(bind=engine)
    yield
    # Clean up after tests
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def mock_s3():
    mock = MagicMock()

    def mock_list_objects_v2(**kwargs):
        if kwargs.get("Bucket") != test_settings.S3_BUCKET:
            raise ClientError(
                {"Error": {"Code": "InvalidAccessKeyId", "Message": "Access Denied"}},
                "ListObjectsV2"
            )
        return {'Contents': [{'Key': 'test.json'}], 'KeyCount': 1}

    def mock_get_object(**kwargs):
        if kwargs.get("Bucket") != test_settings.S3_BUCKET:
            raise ClientError(
                {"Error": {"Code": "InvalidAccessKeyId", "Message": "Access Denied"}},
                "GetObject"
            )
        test_data = [
            {"icao": "A320", "altitude": 30000, "speed": 500}
        ]
        return {
            'Body': MagicMock(read=MagicMock(return_value=json.dumps(test_data).encode()))
        }

    mock.list_objects_v2.side_effect = mock_list_objects_v2
    mock.get_object.side_effect = mock_get_object
    return mock

@pytest.fixture
def client(mock_s3, test_db):
    app.dependency_overrides[get_db] = lambda: test_db
    app.dependency_overrides[get_s3_client] = lambda: mock_s3

    with TestClient(app) as client:
        yield client

def test_get_aircraft_stats_not_found(client):
    response = client.get("/aircraft/B747/stats")
    assert response.status_code == 404
    assert response.json() == {"detail": "Aircraft not found"}

def test_process_s3_data(client):
    response = client.post("/process-s3-data")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Data processed successfully"
    assert "records_processed" in data

def test_get_aircraft_stats_found(client):
    client.post("/process-s3-data")
    response = client.get("/aircraft/A320/stats")
    assert response.status_code == 200
    stats = response.json()
    assert stats["icao"] == "A320"
    assert stats["avg_altitude"] == 30000
    assert stats["avg_speed"] == 500
    assert stats["total_flights"] == 1
