import sys
from pathlib import Path
import copy
from urllib.parse import quote

# Ensure `src` is importable so tests can `import app`
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest
from fastapi.testclient import TestClient
from app import app, activities

client = TestClient(app)


@pytest.fixture(autouse=True)
def isolate_activities():
    """Arrange: snapshot the in-memory activities and restore after each test."""
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


def test_get_activities():
    # Arrange: fixture provides a clean snapshot
    # Act
    resp = client.get("/activities")
    # Assert
    assert resp.status_code == 200
    data = resp.json()
    assert "Chess Club" in data
    assert isinstance(data["Chess Club"]["participants"], list)


def test_signup_and_prevent_duplicate():
    # Arrange
    activity = "Chess Club"
    email = "tester@example.com"
    assert email not in activities[activity]["participants"]

    # Act: sign up
    resp = client.post(f"/activities/{quote(activity)}/signup", params={"email": email})
    # Assert
    assert resp.status_code == 200
    assert email in activities[activity]["participants"]

    # Act: try to sign up again
    resp2 = client.post(f"/activities/{quote(activity)}/signup", params={"email": email})
    # Assert: duplicate prevented
    assert resp2.status_code == 400


def test_remove_participant():
    # Arrange
    activity = "Chess Club"
    email = "michael@mergington.edu"
    assert email in activities[activity]["participants"]

    # Act
    resp = client.delete(f"/activities/{quote(activity)}/participants", params={"email": email})

    # Assert
    assert resp.status_code == 200
    assert email not in activities[activity]["participants"]


def test_activity_full():
    # Arrange: create a tiny activity that's already full
    activity = "Tiny Club"
    activities[activity] = {
        "description": "test",
        "schedule": "now",
        "max_participants": 2,
        "participants": ["a@x.com", "b@x.com"],
    }

    # Act: try to sign up another student
    resp = client.post(f"/activities/{quote(activity)}/signup", params={"email": "c@x.com"})

    # Assert
    assert resp.status_code == 400
