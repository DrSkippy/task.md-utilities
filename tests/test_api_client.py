"""Tests for task_lib/api_client.py."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from task_lib.api_client import (
    APIConnectionError,
    APIHTTPError,
    APITimeoutError,
    api_call,
    resolve_api_url,
    task_url,
)


# ---------------------------------------------------------------------------
# resolve_api_url
# ---------------------------------------------------------------------------


def test_resolve_api_url_flag():
    assert resolve_api_url("http://custom:1234") == "http://custom:1234"


def test_resolve_api_url_flag_strips_trailing_slash():
    assert resolve_api_url("http://custom:1234/") == "http://custom:1234"


def test_resolve_api_url_env():
    with patch.dict("os.environ", {"TASKS_API_URL": "http://remote:9000"}):
        assert resolve_api_url(None) == "http://remote:9000"


def test_resolve_api_url_default():
    # Patch out env var lookup and config file so neither matches
    mock_config_path = MagicMock()
    mock_config_path.exists.return_value = False
    # Chain: Path.home() / ".config" / "tasks" / "config.yaml" → mock_config_path
    mock_home = MagicMock()
    mock_home.__truediv__ = MagicMock(return_value=mock_home)
    mock_home.exists.return_value = False

    with patch("task_lib.api_client.os.getenv", return_value=None), \
         patch("task_lib.api_client.Path") as mock_path_cls:
        mock_path_cls.home.return_value = mock_home
        url = resolve_api_url(None)
    assert url == "http://localhost:3101"


# ---------------------------------------------------------------------------
# task_url
# ---------------------------------------------------------------------------


def test_task_url_encodes_spaces():
    assert task_url("http://host", "My Task") == "http://host/tasks/My%20Task"


def test_task_url_encodes_slash():
    assert task_url("http://host", "a/b") == "http://host/tasks/a%2Fb"


# ---------------------------------------------------------------------------
# api_call — success paths
# ---------------------------------------------------------------------------


def _make_resp(status_code=200, json_data=None, content=b"x"):
    resp = MagicMock()
    resp.status_code = status_code
    resp.content = content
    resp.json.return_value = json_data or {}
    resp.raise_for_status = MagicMock()
    return resp


def test_api_call_returns_json():
    with patch("requests.request", return_value=_make_resp(200, {"key": "val"})):
        result = api_call("GET", "http://host/tasks")
    assert result == {"key": "val"}


def test_api_call_204_returns_empty_dict():
    with patch("requests.request", return_value=_make_resp(204, content=b"")):
        result = api_call("DELETE", "http://host/tasks/foo")
    assert result == {}


# ---------------------------------------------------------------------------
# api_call — error paths
# ---------------------------------------------------------------------------


def test_api_call_connection_error_raises():
    with patch("requests.request", side_effect=requests.exceptions.ConnectionError("refused")):
        with pytest.raises(APIConnectionError):
            api_call("GET", "http://host/tasks")


def test_api_call_timeout_raises():
    with patch("requests.request", side_effect=requests.exceptions.Timeout("timed out")):
        with pytest.raises(APITimeoutError):
            api_call("GET", "http://host/tasks")


def test_api_call_http_error_raises_with_status():
    mock_resp = _make_resp(404, {"error": "Not found"})
    mock_resp.raise_for_status.side_effect = requests.exceptions.HTTPError(
        response=mock_resp
    )
    with patch("requests.request", return_value=mock_resp):
        with pytest.raises(APIHTTPError) as exc_info:
            api_call("GET", "http://host/tasks/missing")
    assert exc_info.value.status_code == 404
    assert "Not found" in exc_info.value.message


def test_api_call_http_error_uses_detail_field():
    mock_resp = _make_resp(422, {"detail": "Validation failed"})
    mock_resp.raise_for_status.side_effect = requests.exceptions.HTTPError(
        response=mock_resp
    )
    with patch("requests.request", return_value=mock_resp):
        with pytest.raises(APIHTTPError) as exc_info:
            api_call("POST", "http://host/tasks")
    assert "Validation failed" in exc_info.value.message
