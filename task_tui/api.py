"""Synchronous API wrappers for use inside Textual workers."""

from __future__ import annotations

from typing import Optional

from task_lib.api_client import api_call, task_url


def fetch_tasks(
    base: str,
    lane: Optional[str] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None,
) -> list[dict]:
    """Fetch all tasks, optionally filtered."""
    params: dict = {}
    if lane:
        params["lane"] = lane
    if tag:
        params["tag"] = tag
    if search:
        params["search"] = search
    result = api_call("GET", f"{base}/tasks", params=params)
    return result if isinstance(result, list) else []


def fetch_lanes(base: str) -> list[dict]:
    """Fetch all lanes with task counts."""
    data = api_call("GET", f"{base}/lanes")
    return data.get("lanes", [])


def fetch_task(base: str, title: str) -> dict:
    """Fetch a single task by title."""
    return api_call("GET", task_url(base, title))


def create_task(base: str, payload: dict) -> dict:
    """Create a new task."""
    return api_call("POST", f"{base}/tasks", json=payload)


def update_task(base: str, title: str, payload: dict) -> dict:
    """Update an existing task."""
    return api_call("PUT", task_url(base, title), json=payload)


def delete_task(base: str, title: str) -> None:
    """Delete (soft) a task by moving it to Trash."""
    api_call("DELETE", task_url(base, title))


def move_task(base: str, title: str, new_lane: str) -> dict:
    """Move a task to a different lane."""
    return api_call("POST", f"{task_url(base, title)}/move", json={"lane": new_lane})
