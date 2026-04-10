"""Shared HTTP client helpers for the task REST API."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional
from urllib.parse import quote

import requests
import yaml


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class APIError(Exception):
    """Base class for all API client errors."""


class APIConnectionError(APIError):
    """Raised when the API server cannot be reached."""


class APITimeoutError(APIError):
    """Raised when a request to the API times out."""


class APIHTTPError(APIError):
    """Raised when the API returns an HTTP error response."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message


# ---------------------------------------------------------------------------
# Config resolution
# ---------------------------------------------------------------------------


def resolve_api_url(flag_value: Optional[str]) -> str:
    """Return the API base URL from the first available source.

    Resolution order:
      1. flag_value argument
      2. TASKS_API_URL environment variable
      3. ~/.config/tasks/config.yaml  →  api_url key
      4. Default: http://localhost:3101
    """
    if flag_value:
        return flag_value.rstrip("/")
    if env := os.getenv("TASKS_API_URL"):
        return env.rstrip("/")
    config_path = Path.home() / ".config" / "tasks" / "config.yaml"
    if config_path.exists():
        data: dict = yaml.safe_load(config_path.read_text()) or {}
        if url := data.get("api_url"):
            return url.rstrip("/")
    return "http://localhost:3101"


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------


def api_call(method: str, url: str, **kwargs: Any) -> Any:
    """Make an HTTP request and return parsed JSON.

    Raises:
        APIConnectionError: if the server cannot be reached.
        APITimeoutError: if the request times out.
        APIHTTPError: if the server returns an HTTP error status.
    """
    try:
        resp = requests.request(method, url, timeout=15, **kwargs)
        resp.raise_for_status()
        if resp.status_code == 204 or not resp.content:
            return {}
        return resp.json()
    except requests.exceptions.ConnectionError as exc:
        raise APIConnectionError(f"Cannot connect to API at {url}") from exc
    except requests.exceptions.Timeout as exc:
        raise APITimeoutError("Request timed out") from exc
    except requests.exceptions.HTTPError as exc:
        body: dict = {}
        try:
            body = exc.response.json()
        except Exception:
            pass
        msg = body.get("error") or body.get("detail") or str(exc)
        raise APIHTTPError(status_code=exc.response.status_code, message=msg) from exc


def task_url(base: str, title: str) -> str:
    """Build the URL for a specific task by title."""
    return f"{base}/tasks/{quote(title, safe='')}"
