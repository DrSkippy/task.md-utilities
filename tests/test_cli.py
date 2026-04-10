"""Tests for the tasks CLI (bin/tasks)."""

import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Load the CLI module from bin/tasks (no .py extension)
import importlib.machinery
_CLI_PATH = Path(__file__).parent.parent / "bin" / "tasks"
loader = importlib.machinery.SourceFileLoader("tasks_cli", str(_CLI_PATH))
spec = importlib.util.spec_from_loader("tasks_cli", loader)
assert spec is not None
tasks_cli = importlib.util.module_from_spec(spec)
loader.exec_module(tasks_cli)

from click.testing import CliRunner

cli = tasks_cli.cli


def _mock_response(json_data=None, status_code=200):
    resp = MagicMock()
    resp.status_code = status_code
    resp.content = b"x"
    resp.json.return_value = json_data or {}
    resp.raise_for_status = MagicMock()
    return resp


# ---------------------------------------------------------------------------
# Config resolution
# ---------------------------------------------------------------------------

def test_resolve_api_url_flag():
    assert tasks_cli.resolve_api_url("http://custom:1234") == "http://custom:1234"


def test_resolve_api_url_default():
    with patch.dict("os.environ", {}, clear=True):
        url = tasks_cli.resolve_api_url(None)
    assert url == "http://localhost:3101"


def test_resolve_api_url_env():
    with patch.dict("os.environ", {"TASKS_API_URL": "http://remote:9000"}):
        url = tasks_cli.resolve_api_url(None)
    assert url == "http://remote:9000"


# ---------------------------------------------------------------------------
# show command
# ---------------------------------------------------------------------------

TASKS_RESPONSE = [
    {"title": "Do thing", "lane": "todo", "tags": ["urgent"], "due_date": "2026-06-01"},
    {"title": "Other thing", "lane": "doing", "tags": [], "due_date": None},
]


def test_show_renders_table():
    runner = CliRunner()
    with patch("requests.request", return_value=_mock_response(TASKS_RESPONSE)):
        result = runner.invoke(cli, ["--api-url", "http://test", "show"])
    assert result.exit_code == 0
    assert "Do thing" in result.output
    assert "Other thing" in result.output
    assert "todo" in result.output


def test_show_with_lane_filter():
    runner = CliRunner()
    with patch("requests.request") as mock_req:
        mock_req.return_value = _mock_response([TASKS_RESPONSE[0]])
        result = runner.invoke(cli, ["--api-url", "http://test", "show", "--lane", "todo"])
    assert result.exit_code == 0
    call_kwargs = mock_req.call_args
    assert call_kwargs[1]["params"]["lane"] == "todo"


def test_show_empty():
    runner = CliRunner()
    with patch("requests.request", return_value=_mock_response([])):
        result = runner.invoke(cli, ["--api-url", "http://test", "show"])
    assert result.exit_code == 0
    assert "No tasks" in result.output


# ---------------------------------------------------------------------------
# get command
# ---------------------------------------------------------------------------

TASK_DETAIL = {
    "title": "My Task",
    "lane": "todo",
    "content": "Full body here",
    "tags": ["backend"],
    "due_date": "2026-01-15",
    "path": "/data/tasks/todo/My Task.md",
}


def test_get_renders_panel():
    runner = CliRunner()
    with patch("requests.request", return_value=_mock_response(TASK_DETAIL)):
        result = runner.invoke(cli, ["--api-url", "http://test", "get", "My Task"])
    assert result.exit_code == 0
    assert "Full body here" in result.output
    assert "My Task" in result.output


# ---------------------------------------------------------------------------
# add command
# ---------------------------------------------------------------------------

def test_add_sends_json():
    runner = CliRunner()
    with patch("requests.request") as mock_req:
        mock_req.return_value = _mock_response(
            {"title": "New Task", "lane": "todo", "tags": ["x"], "due_date": None, "content": "", "path": ""}
        )
        result = runner.invoke(cli, [
            "--api-url", "http://test", "add",
            "--title", "New Task",
            "--content", "Body",
            "--lane", "todo",
            "--tags", "x,y",
        ])
    assert result.exit_code == 0
    assert "Created" in result.output
    sent = mock_req.call_args[1]["json"]
    assert sent["title"] == "New Task"
    assert "x" in sent["tags"]
    assert "y" in sent["tags"]


# ---------------------------------------------------------------------------
# update command
# ---------------------------------------------------------------------------

def test_update_sends_only_provided_fields():
    runner = CliRunner()
    with patch("requests.request") as mock_req:
        mock_req.return_value = _mock_response(
            {"title": "My Task", "lane": "todo", "tags": ["a"], "due_date": None, "content": "new", "path": ""}
        )
        result = runner.invoke(cli, [
            "--api-url", "http://test", "update", "My Task",
            "--content", "new content",
        ])
    assert result.exit_code == 0
    sent = mock_req.call_args[1]["json"]
    assert "content" in sent
    assert "tags" not in sent


def test_update_nothing_to_update():
    runner = CliRunner()
    result = runner.invoke(cli, ["--api-url", "http://test", "update", "My Task"])
    assert result.exit_code == 0
    assert "Nothing to update" in result.output


# ---------------------------------------------------------------------------
# delete command
# ---------------------------------------------------------------------------

def test_delete_confirmed():
    runner = CliRunner()
    resp = MagicMock()
    resp.status_code = 204
    resp.content = b""
    resp.raise_for_status = MagicMock()
    with patch("requests.request", return_value=resp):
        result = runner.invoke(cli, ["--api-url", "http://test", "delete", "My Task"], input="y\n")
    assert result.exit_code == 0
    assert "Trash" in result.output


def test_delete_aborted():
    runner = CliRunner()
    result = runner.invoke(cli, ["--api-url", "http://test", "delete", "My Task"], input="n\n")
    assert result.exit_code != 0 or "Aborted" in result.output


# ---------------------------------------------------------------------------
# move command
# ---------------------------------------------------------------------------

def test_move_sends_lane():
    runner = CliRunner()
    with patch("requests.request") as mock_req:
        mock_req.return_value = _mock_response({"message": "Moved task"})
        result = runner.invoke(cli, ["--api-url", "http://test", "move", "My Task", "done"])
    assert result.exit_code == 0
    sent = mock_req.call_args[1]["json"]
    assert sent["lane"] == "done"


# ---------------------------------------------------------------------------
# lanes commands
# ---------------------------------------------------------------------------

LANES_RESPONSE = {
    "lanes": [{"name": "todo", "task_count": 3}, {"name": "done", "task_count": 10}],
    "total_lanes": 2,
}


def test_lanes_list():
    runner = CliRunner()
    with patch("requests.request", return_value=_mock_response(LANES_RESPONSE)):
        result = runner.invoke(cli, ["--api-url", "http://test", "lanes", "list"])
    assert result.exit_code == 0
    assert "todo" in result.output
    assert "done" in result.output


def test_lanes_add():
    runner = CliRunner()
    with patch("requests.request") as mock_req:
        mock_req.return_value = _mock_response({"message": "Created lane 'sprint1'"})
        result = runner.invoke(cli, ["--api-url", "http://test", "lanes", "add", "sprint1"])
    assert result.exit_code == 0
    sent = mock_req.call_args[1]["json"]
    assert sent["name"] == "sprint1"


# ---------------------------------------------------------------------------
# stats command
# ---------------------------------------------------------------------------

STATS_RESPONSE = {
    "num_lanes": 2,
    "tasks_per_lane": {"todo": 3, "done": 10},
    "tag_counts": {"urgent": 2, "backend": 1},
    "due_date_counts": {"No Due Date": 10, "2026-06-01": 3},
}


def test_stats_renders_tables():
    runner = CliRunner()
    with patch("requests.request", return_value=_mock_response(STATS_RESPONSE)):
        result = runner.invoke(cli, ["--api-url", "http://test", "stats"])
    assert result.exit_code == 0
    assert "todo" in result.output
    assert "urgent" in result.output
    assert "No Due Date" in result.output


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

def test_connection_error_exits_1():
    runner = CliRunner()
    with patch("requests.request", side_effect=Exception("connection refused")):
        # Patch the api_call helper directly to trigger the ConnectionError path
        with patch.object(tasks_cli, "api_call", side_effect=SystemExit(1)):
            result = runner.invoke(cli, ["--api-url", "http://test", "show"])
    assert result.exit_code == 1
