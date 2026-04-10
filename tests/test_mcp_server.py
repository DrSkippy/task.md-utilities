"""Tests for the improved MCP server tool functions."""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

# Patch TASK_CONFIG_PATH before importing server so get_task_manager doesn't
# try to read a non-existent config file on import.
import os
os.environ.setdefault("TASK_CONFIG_PATH", "/nonexistent/config.yaml")

# We import the tool functions directly — no transport layer needed.
import mcp_task_service.server as srv


@pytest.fixture(autouse=True)
def reset_task_manager():
    """Reset the singleton between tests."""
    srv._task_manager = None
    yield
    srv._task_manager = None


@pytest.fixture()
def task_dir(tmp_path):
    """Provide a tmpdir and wire the server's TaskManager to use it."""
    from task_lib.config import Config
    from task_lib.task_manager import TaskManager

    cfg = Config()
    cfg.base_dir = tmp_path
    tm = TaskManager(cfg)

    (tmp_path / "todo").mkdir(exist_ok=True)
    (tmp_path / "doing").mkdir(exist_ok=True)

    srv._task_manager = tm
    return tmp_path


# ---------------------------------------------------------------------------
# add_task (replaces add_task_from_json)
# ---------------------------------------------------------------------------

def test_add_task_basic(task_dir):
    result = srv.add_task(title="My Task", content="Do the thing", lane="todo")
    assert "My Task" in result
    assert (task_dir / "todo" / "My Task.md").exists()


def test_add_task_with_tags_and_due(task_dir):
    result = srv.add_task(
        title="Tagged", content="Body", lane="todo",
        tags=["urgent", "bug"], due_date="2026-06-01"
    )
    assert "Tagged" in result
    content = (task_dir / "todo" / "Tagged.md").read_text()
    assert "[tag:urgent]" in content
    assert "[due:2026-06-01]" in content


def test_add_task_bad_due_date(task_dir):
    result = srv.add_task(title="Bad", content="x", lane="todo", due_date="not-a-date")
    assert "Error" in result


# ---------------------------------------------------------------------------
# get_task
# ---------------------------------------------------------------------------

def test_get_task(task_dir):
    srv.add_task("Find Me", "content here", "todo")
    data = json.loads(srv.get_task("Find Me"))
    assert data["title"] == "Find Me"
    assert data["lane"] == "todo"


def test_get_task_not_found(task_dir):
    data = json.loads(srv.get_task("Ghost"))
    assert "error" in data


# ---------------------------------------------------------------------------
# update_task — tags are now List[str], not comma-string
# ---------------------------------------------------------------------------

def test_update_task_tags_as_list(task_dir):
    srv.add_task("Upd Task", "body", "todo")
    result = srv.update_task("Upd Task", tags=["feature", "backend"])
    assert "Successfully" in result
    data = json.loads(srv.get_task("Upd Task"))
    assert "feature" in data["tags"]
    assert "backend" in data["tags"]


def test_update_task_content(task_dir):
    srv.add_task("Edit Me", "old content", "todo")
    srv.update_task("Edit Me", content="new content")
    data = json.loads(srv.get_task("Edit Me"))
    assert data["content"] == "new content"


def test_update_task_rename(task_dir):
    srv.add_task("Old Name", "body", "todo")
    srv.update_task("Old Name", new_title="New Name")
    assert not (task_dir / "todo" / "Old Name.md").exists()
    assert (task_dir / "todo" / "New Name.md").exists()


def test_update_task_clear_due_date(task_dir):
    srv.add_task("Dated", "body", "todo", due_date="2026-01-01")
    srv.update_task("Dated", due_date="")  # empty string clears
    data = json.loads(srv.get_task("Dated"))
    assert data["due_date"] is None


def test_update_task_not_found(task_dir):
    result = srv.update_task("Ghost", content="x")
    assert "Error" in result


# ---------------------------------------------------------------------------
# delete_task
# ---------------------------------------------------------------------------

def test_delete_task(task_dir):
    srv.add_task("Delete Me", "body", "todo")
    result = srv.delete_task("Delete Me")
    assert "Trash" in result
    assert (task_dir / "Trash" / "Delete Me.md").exists()
    assert not (task_dir / "todo" / "Delete Me.md").exists()


def test_delete_task_not_found(task_dir):
    result = srv.delete_task("Ghost")
    assert "Error" in result


# ---------------------------------------------------------------------------
# add_lane
# ---------------------------------------------------------------------------

def test_add_lane(task_dir):
    result = srv.add_lane("sprint1")
    assert "sprint1" in result
    assert (task_dir / "sprint1").is_dir()


# ---------------------------------------------------------------------------
# list_tasks / list_lanes
# ---------------------------------------------------------------------------

def test_list_tasks_all(task_dir):
    srv.add_task("A", "a", "todo")
    srv.add_task("B", "b", "doing")
    data = json.loads(srv.list_tasks())
    titles = [t["title"] for t in data["tasks"]]
    assert "A" in titles
    assert "B" in titles


def test_list_tasks_filter_lane(task_dir):
    srv.add_task("A", "a", "todo")
    srv.add_task("B", "b", "doing")
    data = json.loads(srv.list_tasks(lane="todo"))
    titles = [t["title"] for t in data["tasks"]]
    assert "A" in titles
    assert "B" not in titles


def test_list_tasks_filter_tag(task_dir):
    srv.add_task("Tagged", "t", "todo", tags=["urgent"])
    srv.add_task("Plain", "p", "todo")
    data = json.loads(srv.list_tasks(tag="urgent"))
    titles = [t["title"] for t in data["tasks"]]
    assert "Tagged" in titles
    assert "Plain" not in titles


def test_list_lanes(task_dir):
    data = json.loads(srv.list_lanes())
    names = [l["name"] for l in data["lanes"]]
    assert "todo" in names
    assert "doing" in names


# ---------------------------------------------------------------------------
# empty_trash
# ---------------------------------------------------------------------------

def test_empty_trash(task_dir):
    srv.add_task("Trash Me", "body", "todo")
    srv.delete_task("Trash Me")
    assert (task_dir / "Trash" / "Trash Me.md").exists()
    srv.empty_trash()
    assert not list((task_dir / "Trash").glob("*.md"))


# ---------------------------------------------------------------------------
# split_tasks
# ---------------------------------------------------------------------------

def test_split_tasks_no_split_marker(task_dir):
    srv.add_task("Normal Task", "no marker here", "todo")
    result = srv.split_tasks()
    assert "No tasks" in result


def test_split_tasks_with_marker(task_dir):
    srv.add_task("Big Task", "Part A [[split]] Part B [[split]] Part C", "todo")
    result = json.loads(srv.split_tasks())
    assert result["tasks_split"] == 1
    assert result["total_tasks_after"] == 3


# ---------------------------------------------------------------------------
# get_statistics
# ---------------------------------------------------------------------------

def test_get_statistics(task_dir):
    srv.add_task("S1", "body", "todo", tags=["x"])
    srv.add_task("S2", "body", "todo")
    data = json.loads(srv.get_statistics())
    assert "num_lanes" in data
    assert data["tasks_per_lane"].get("todo", 0) >= 2
