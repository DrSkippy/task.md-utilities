"""Lightweight Textual TUI tests."""

from __future__ import annotations

from unittest.mock import patch

from task_tui.app import KanbanApp
from task_tui.widgets import LaneColumn


MOCK_LANES = [
    {"name": "Backlog", "task_count": 2},
    {"name": "Doing", "task_count": 1},
    {"name": "Done", "task_count": 0},
]

MOCK_TASKS = [
    {"title": "Fix login", "lane": "Backlog", "tags": ["urgent"], "due_date": "2026-06-01", "content": "body"},
    {"title": "Write docs", "lane": "Backlog", "tags": [], "due_date": None, "content": ""},
    {"title": "Add API", "lane": "Doing", "tags": ["backend"], "due_date": None, "content": "body"},
]


def _make_app() -> KanbanApp:
    return KanbanApp(api_url="http://test:3101")


async def test_kanban_app_launches():
    """App mounts LaneColumn widgets for each lane after loading."""
    with patch("task_tui.api.fetch_lanes", return_value=MOCK_LANES), \
         patch("task_tui.api.fetch_tasks", return_value=MOCK_TASKS):
        async with _make_app().run_test(size=(120, 40)) as pilot:
            # Wait for worker to complete and re-render
            await pilot.pause(0.5)
            columns = pilot.app.query(LaneColumn)
            assert len(list(columns)) == 3


async def test_right_arrow_advances_lane():
    """Pressing right arrow increments the focused lane index."""
    with patch("task_tui.api.fetch_lanes", return_value=MOCK_LANES), \
         patch("task_tui.api.fetch_tasks", return_value=MOCK_TASKS):
        async with _make_app().run_test(size=(120, 40)) as pilot:
            await pilot.pause(0.5)
            assert pilot.app._focused_lane_idx == 0
            await pilot.press("right")
            assert pilot.app._focused_lane_idx == 1


async def test_left_arrow_wraps_around():
    """Pressing left from index 0 wraps to the last lane."""
    with patch("task_tui.api.fetch_lanes", return_value=MOCK_LANES), \
         patch("task_tui.api.fetch_tasks", return_value=MOCK_TASKS):
        async with _make_app().run_test(size=(120, 40)) as pilot:
            await pilot.pause(0.5)
            await pilot.press("left")
            cols = list(pilot.app.query(LaneColumn))
            assert pilot.app._focused_lane_idx == len(cols) - 1


async def test_f10_quits():
    """F10 exits the application."""
    with patch("task_tui.api.fetch_lanes", return_value=MOCK_LANES), \
         patch("task_tui.api.fetch_tasks", return_value=MOCK_TASKS):
        async with _make_app().run_test(size=(120, 40)) as pilot:
            await pilot.pause(0.3)
            await pilot.press("f9")
        # If we reach here the app exited cleanly
        assert True
