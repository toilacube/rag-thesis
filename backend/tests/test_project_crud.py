import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.models.models import Base, Project
from db.database import get_db_session

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db_session():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db_session] = override_get_db_session

Base.metadata.create_all(bind=engine)

client = TestClient(app)

@pytest.fixture
def test_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield

def test_create_project(test_db):
    response = client.post(
        "/api/project",
        json={"project_name": "Test Project", "description": "Test Description"},
    )
    assert response.status_code == 201
    assert response.json()["project_name"] == "Test Project"
    assert response.json()["description"] == "Test Description"

def test_get_projects(test_db):
    client.post(
        "/api/project",
        json={"project_name": "Test Project", "description": "Test Description"},
    )
    response = client.get("/api/project")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["project_name"] == "Test Project"

def test_get_project_by_id(test_db):
    create_response = client.post(
        "/api/project",
        json={"project_name": "Test Project", "description": "Test Description"},
    )
    project_id = create_response.json()["id"]
    response = client.get(f"/api/project/{project_id}")
    assert response.status_code == 200
    assert response.json()["project_name"] == "Test Project"

def test_update_project(test_db):
    create_response = client.post(
        "/api/project",
        json={"project_name": "Test Project", "description": "Test Description"},
    )
    project_id = create_response.json()["id"]
    response = client.put(
        f"/api/project/{project_id}",
        json={"project_name": "Updated Project", "description": "Updated Description"},
    )
    assert response.status_code == 200
    assert response.json()["project_name"] == "Updated Project"
    assert response.json()["description"] == "Updated Description"

def test_delete_project(test_db):
    create_response = client.post(
        "/api/project",
        json={"project_name": "Test Project", "description": "Test Description"},
    )
    project_id = create_response.json()["id"]
    response = client.delete(f"/api/project/{project_id}")
    assert response.status_code == 204
    get_response = client.get(f"/api/project/{project_id}")
    assert get_response.status_code == 404