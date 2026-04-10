"""Tests for the Task REST API (task_api/)."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure task_lib and task_api are importable
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from task_api.app import create_app
from task_lib.config import Config
from task_lib.task_manager import TaskManager


@pytest.fixture()
def app(tmp_path):
    """Create a Flask test app with a temporary task directory."""
    (tmp_path / "todo").mkdir()
    (tmp_path / "doing").mkdir()

    lib_cfg = Config()
    lib_cfg.base_dir = tmp_path
    tm = TaskManager(lib_cfg)

    with patch("task_api.config.ApiConfig.__init__", return_value=None), \
         patch("task_api.config.ApiConfig.base_dir", new=tmp_path, create=True):
        flask_app = create_app.__wrapped__() if hasattr(create_app, "__wrapped__") else _make_app(tmp_path)

    flask_app.config["TESTING"] = True
    flask_app.config["TASK_MANAGER"] = tm
    return flask_app


def _make_app(base_dir: Path):
    """Build the Flask app directly, bypassing ApiConfig file loading."""
    from flask import Flask
    from task_api.routes.health import health_bp
    from task_api.routes.tasks import tasks_bp
    from task_api.routes.lanes import lanes_bp
    from task_api.routes.operations import ops_bp

    app = Flask(__name__)
    lib_cfg = Config()
    lib_cfg.base_dir = base_dir
    app.config["TASK_MANAGER"] = TaskManager(lib_cfg)
    app.register_blueprint(health_bp)
    app.register_blueprint(tasks_bp, url_prefix="/tasks")
    app.register_blueprint(lanes_bp, url_prefix="/lanes")
    app.register_blueprint(ops_bp, url_prefix="/operations")
    return app


@pytest.fixture()
def app(tmp_path):
    flask_app = _make_app(tmp_path)
    flask_app.config["TESTING"] = True
    return flask_app


@pytest.fixture()
def client(app):
    return app.test_client()


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json()["status"] == "ok"


# ---------------------------------------------------------------------------
# Lanes
# ---------------------------------------------------------------------------

def test_list_lanes_empty(client):
    r = client.get("/lanes")
    assert r.status_code == 200
    data = r.get_json()
    assert data["total_lanes"] == 0
    assert data["lanes"] == []


def test_create_lane(client):
    r = client.post("/lanes", json={"name": "Backlog"})
    assert r.status_code == 201
    assert "Backlog" in r.get_json()["message"]


def test_create_lane_missing_name(client):
    r = client.post("/lanes", json={})
    assert r.status_code == 422


def test_list_lanes_after_create(client):
    client.post("/lanes", json={"name": "Backlog"})
    r = client.get("/lanes")
    assert r.status_code == 200
    names = [l["name"] for l in r.get_json()["lanes"]]
    assert "Backlog" in names


# ---------------------------------------------------------------------------
# Tasks — create
# ---------------------------------------------------------------------------

def test_create_task(client):
    client.post("/lanes", json={"name": "todo"})
    r = client.post("/tasks", json={
        "title": "First Task",
        "content": "Do the thing",
        "lane": "todo",
    })
    assert r.status_code == 201
    data = r.get_json()
    assert data["title"] == "First Task"
    assert data["lane"] == "todo"
    assert data["tags"] == []
    assert data["due_date"] is None


def test_create_task_with_tags_and_due(client):
    client.post("/lanes", json={"name": "todo"})
    r = client.post("/tasks", json={
        "title": "Tagged Task",
        "content": "Body",
        "lane": "todo",
        "tags": ["urgent", "bug"],
        "due_date": "2026-12-31",
    })
    assert r.status_code == 201
    data = r.get_json()
    assert data["tags"] == ["urgent", "bug"]
    assert data["due_date"] == "2026-12-31"


def test_create_task_missing_required_field(client):
    r = client.post("/tasks", json={"title": "No lane"})
    assert r.status_code == 422


def test_create_task_invalid_due_date(client):
    client.post("/lanes", json={"name": "todo"})
    r = client.post("/tasks", json={
        "title": "Bad Date",
        "content": "body",
        "lane": "todo",
        "due_date": "not-a-date",
    })
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# Tasks — read
# ---------------------------------------------------------------------------

def _seed_task(client, title="My Task", lane="todo", tags=None):
    client.post("/lanes", json={"name": lane})
    client.post("/tasks", json={
        "title": title,
        "content": "Content here",
        "lane": lane,
        "tags": tags or [],
    })


def test_get_task(client):
    _seed_task(client)
    r = client.get("/tasks/My%20Task")
    assert r.status_code == 200
    assert r.get_json()["title"] == "My Task"


def test_get_task_not_found(client):
    r = client.get("/tasks/Nonexistent")
    assert r.status_code == 404


def test_list_tasks_returns_all(client):
    _seed_task(client, "Task A", "todo")
    _seed_task(client, "Task B", "doing")
    r = client.get("/tasks")
    assert r.status_code == 200
    titles = [t["title"] for t in r.get_json()]
    assert "Task A" in titles
    assert "Task B" in titles


def test_list_tasks_filter_by_lane(client):
    _seed_task(client, "Task A", "todo")
    _seed_task(client, "Task B", "doing")
    r = client.get("/tasks?lane=todo")
    assert r.status_code == 200
    titles = [t["title"] for t in r.get_json()]
    assert "Task A" in titles
    assert "Task B" not in titles


def test_list_tasks_filter_by_tag(client):
    _seed_task(client, "Tagged", "todo", tags=["urgent"])
    _seed_task(client, "Untagged", "todo")
    r = client.get("/tasks?tag=urgent")
    titles = [t["title"] for t in r.get_json()]
    assert "Tagged" in titles
    assert "Untagged" not in titles


# ---------------------------------------------------------------------------
# Tasks — update
# ---------------------------------------------------------------------------

def test_update_task_content(client):
    _seed_task(client)
    r = client.put("/tasks/My%20Task", json={"content": "New content"})
    assert r.status_code == 200
    assert r.get_json()["content"] == "New content"


def test_update_task_tags_as_list(client):
    _seed_task(client)
    r = client.put("/tasks/My%20Task", json={"tags": ["feature", "backend"]})
    assert r.status_code == 200
    assert r.get_json()["tags"] == ["feature", "backend"]


def test_update_task_rename(client):
    _seed_task(client)
    r = client.put("/tasks/My%20Task", json={"new_title": "Renamed Task"})
    assert r.status_code == 200
    assert r.get_json()["title"] == "Renamed Task"
    # Old title should be gone
    r2 = client.get("/tasks/My%20Task")
    assert r2.status_code == 404


def test_update_task_clear_due_date(client):
    client.post("/lanes", json={"name": "todo"})
    client.post("/tasks", json={
        "title": "Dated Task", "content": "x", "lane": "todo", "due_date": "2026-01-01"
    })
    r = client.put("/tasks/Dated%20Task", json={"due_date": None})
    assert r.status_code == 200
    assert r.get_json()["due_date"] is None


def test_update_task_not_found(client):
    r = client.put("/tasks/Ghost", json={"content": "x"})
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Tasks — delete / move
# ---------------------------------------------------------------------------

def test_delete_task(client, tmp_path):
    _seed_task(client)
    r = client.delete("/tasks/My%20Task")
    assert r.status_code == 204
    # Should be in Trash now
    assert (tmp_path / "Trash" / "My Task.md").exists()
    # Should no longer appear in list
    r2 = client.get("/tasks/My%20Task")
    assert r2.status_code == 404


def test_delete_task_not_found(client):
    r = client.delete("/tasks/Ghost")
    assert r.status_code == 404


def test_move_task(client):
    _seed_task(client, "Mover", "todo")
    client.post("/lanes", json={"name": "done"})
    r = client.post("/tasks/Mover/move", json={"lane": "done"})
    assert r.status_code == 200
    assert "done" in r.get_json()["message"]
    # Verify new lane
    assert client.get("/tasks/Mover").get_json()["lane"] == "done"


def test_move_task_missing_lane(client):
    _seed_task(client)
    r = client.post("/tasks/My%20Task/move", json={})
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# Operations
# ---------------------------------------------------------------------------

def test_statistics(client):
    _seed_task(client, "Task A", "todo", tags=["x"])
    _seed_task(client, "Task B", "todo")
    r = client.get("/operations/statistics")
    assert r.status_code == 200
    data = r.get_json()
    assert "num_lanes" in data
    assert data["tasks_per_lane"].get("todo", 0) >= 2


def test_empty_trash(client):
    _seed_task(client)
    client.delete("/tasks/My%20Task")
    r = client.delete("/operations/trash")
    assert r.status_code == 200


def test_split_no_tasks(client):
    r = client.post("/operations/split")
    assert r.status_code == 200
    assert "No tasks" in r.get_json()["message"]


def test_split_tasks(client):
    client.post("/lanes", json={"name": "todo"})
    client.post("/tasks", json={
        "title": "Big Task",
        "content": "Part one [[split]] Part two [[split]] Part three",
        "lane": "todo",
    })
    r = client.post("/operations/split")
    assert r.status_code == 200
    data = r.get_json()
    assert data["tasks_split"] == 1
    assert data["total_tasks_after"] == 3
