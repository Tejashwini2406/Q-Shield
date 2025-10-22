import os
import pytest
from fastapi.testclient import TestClient
from server.server import app
from server.database import init, Base
from sqlalchemy import create_engine


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    # Create a module-scoped temp directory for the SQLite file
    temp_dir = tmp_path_factory.mktemp("data")
    db_url = f"sqlite:///{temp_dir}/test.db"
    # Override the DATABASE_URL environment variable
    os.environ["DATABASE_URL"] = db_url
    # Initialize the database (engine, session, tables)
    init()
    # Create tables for all models
    Base.metadata.create_all(bind=create_engine(db_url, echo=False))
    # Return a test client for the FastAPI app
    return TestClient(app)

def test_device_registration_and_telemetry(client):
    response = client.post("/api/v1/register", json={
        "device_type": "sensor",
        "hardware_profile": "standard",
        "location": {"lat":12.34, "lon":56.78},
        "public_key": "aabbccddeeff"
    })
    assert response.status_code == 200

    device_id = response.json().get("device_id")
    telemetry_data = {
        "device_id": str(device_id),
        "encrypted_payload": "deadbeef",
        "signature": "cafebabe",
        "timestamp": 1234567890.0
    }
    headers = {"Authorization": f"Bearer {device_id}"}

    response = client.post("/api/v1/telemetry", json=telemetry_data, headers=headers)

    print("Response JSON:", response.json())
    assert response.status_code == 200