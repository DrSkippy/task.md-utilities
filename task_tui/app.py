"""Textual kanban board application."""

from __future__ import annotations

from typing import Optional

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import ListView

from task_lib.api_client import APIError
from task_tui import api
from task_tui.screens import (
    ConfirmScreen,
    DetailScreen,
    FilterScreen,
    MoveScreen,
    TaskFormScreen,
)
from task_tui.widgets import FunctionKeyBar, LaneColumn


class KanbanApp(App):
    """Full-screen interactive kanban board."""

    TITLE = "HENDRICKSON KANBAN"

    BINDINGS = [
        Binding("f1", "show_help", "Help", show=False),
        Binding("f2", "new_task", "New"),
        Binding("f3", "edit_task", "Edit"),
        Binding("f4", "delete_task", "Delete"),
        Binding("f5", "filter_tasks", "Filter"),
        Binding("f6", "move_task", "Move"),
        Binding("f7", "view_task", "Detail"),
        Binding("f10", "quit", "Quit"),
        Binding("left", "prev_lane", "Prev Lane", show=False),
        Binding("right", "next_lane", "Next Lane", show=False),
        Binding("enter", "view_task", "View", show=False),
    ]

    DEFAULT_CSS = """
    KanbanApp {
        layout: vertical;
    }
    #board {
        layout: horizontal;
        height: 1fr;
    }
    #filter-status {
        dock: top;
        height: 1;
        background: $warning-darken-2;
        color: $text;
        padding: 0 1;
        display: none;
    }
    #filter-status.active {
        display: block;
    }
    """

    def __init__(self, api_url: str) -> None:
        super().__init__()
        self._api_url = api_url
        self._lanes: list[str] = []
        self._tasks_by_lane: dict[str, list[dict]] = {}
        self._filter: dict = {}
        self._focused_lane_idx: int = 0

    # ------------------------------------------------------------------
    # Compose & mount
    # ------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        from textual.widgets import Label
        yield Label("", id="filter-status")
        yield Horizontal(id="board")
        yield FunctionKeyBar()

    def on_mount(self) -> None:
        self.run_worker(self._load_board, exclusive=True, thread=True)

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _load_board(self) -> None:
        """Fetch tasks from the API and group by lane (runs in worker thread)."""
        try:
            lane_data = api.fetch_lanes(self._api_url)
            self._lanes = [l["name"] for l in lane_data]

            tasks = api.fetch_tasks(
                self._api_url,
                lane=self._filter.get("lane"),
                tag=self._filter.get("tag"),
                search=self._filter.get("search"),
            )
        except APIError as e:
            self.call_from_thread(self.notify, str(e), severity="error")
            return

        by_lane: dict[str, list[dict]] = {name: [] for name in self._lanes}
        for task in tasks:
            lane = task.get("lane", "")
            if lane in by_lane:
                by_lane[lane].append(task)
            else:
                # Lane exists in tasks but not in lanes list (e.g. filtered)
                if lane not in by_lane:
                    by_lane[lane] = []
                by_lane[lane].append(task)
                if lane not in self._lanes:
                    self._lanes.append(lane)

        self._tasks_by_lane = by_lane
        self.call_from_thread(self._render_board)

    def _render_board(self) -> None:
        """Re-render the lane columns in the DOM (must run on main thread)."""
        board = self.query_one("#board", Horizontal)
        board.remove_children()

        for lane_name in self._lanes:
            tasks = self._tasks_by_lane.get(lane_name, [])
            board.mount(LaneColumn(lane_name, tasks))

        self._update_filter_status()
        self._restore_focus()

    def _restore_focus(self) -> None:
        """Focus the previously focused lane column."""
        columns = list(self.query(LaneColumn))
        if not columns:
            return
        idx = min(self._focused_lane_idx, len(columns) - 1)
        self._focused_lane_idx = idx
        columns[idx].focus_list()

    def _update_filter_status(self) -> None:
        """Show/hide the active filter status bar."""
        from textual.widgets import Label
        bar = self.query_one("#filter-status", Label)
        active = {k: v for k, v in self._filter.items() if v}
        if active:
            parts = [f"{k}={v}" for k, v in active.items()]
            bar.update(f"Filter: {', '.join(parts)}  (F5 to change)")
            bar.add_class("active")
        else:
            bar.update("")
            bar.remove_class("active")

    # ------------------------------------------------------------------
    # Lane navigation
    # ------------------------------------------------------------------

    def _columns(self) -> list[LaneColumn]:
        return list(self.query(LaneColumn))

    def action_prev_lane(self) -> None:
        cols = self._columns()
        if not cols:
            return
        self._focused_lane_idx = (self._focused_lane_idx - 1) % len(cols)
        cols[self._focused_lane_idx].focus_list()

    def action_next_lane(self) -> None:
        cols = self._columns()
        if not cols:
            return
        self._focused_lane_idx = (self._focused_lane_idx + 1) % len(cols)
        cols[self._focused_lane_idx].focus_list()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _current_column(self) -> Optional[LaneColumn]:
        cols = self._columns()
        if not cols:
            return None
        return cols[self._focused_lane_idx]

    def _current_task(self) -> Optional[dict]:
        col = self._current_column()
        return col.current_task if col else None

    def _current_lane_name(self) -> Optional[str]:
        col = self._current_column()
        return col.lane_name if col else None

    def _reload(self) -> None:
        """Reload the board from the API."""
        self.run_worker(self._load_board, exclusive=True, thread=True)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_show_help(self) -> None:
        self.notify(
            "←/→ Navigate lanes  ↑/↓ Navigate tasks  Enter/F7 Detail  "
            "F2 New  F3 Edit  F4 Delete  F5 Filter  F6 Move  F7 Detail  F10 Quit",
            title="Keyboard Shortcuts",
            timeout=6,
        )

    def action_view_task(self) -> None:
        task = self._current_task()
        if task is None:
            return
        self.push_screen(DetailScreen(task))

    def action_new_task(self) -> None:
        lane_name = self._current_lane_name()
        # Pre-populate the lane field with the currently focused lane
        stub: Optional[dict] = {"lane": lane_name} if lane_name else None
        self.push_screen(
            TaskFormScreen(task=stub, lanes=self._lanes),
            callback=self._on_form_result,
        )

    def action_edit_task(self) -> None:
        task = self._current_task()
        if task is None:
            self.notify("No task selected.", severity="warning")
            return
        self.push_screen(
            TaskFormScreen(task=task, lanes=self._lanes),
            callback=self._on_form_result,
        )

    def action_delete_task(self) -> None:
        task = self._current_task()
        if task is None:
            self.notify("No task selected.", severity="warning")
            return
        self.push_screen(
            ConfirmScreen(f"Move '{task['title']}' to Trash?"),
            callback=self._on_confirm_delete,
        )

    def action_filter_tasks(self) -> None:
        self.push_screen(
            FilterScreen(current=self._filter),
            callback=self._on_filter_result,
        )

    def action_move_task(self) -> None:
        task = self._current_task()
        if task is None:
            self.notify("No task selected.", severity="warning")
            return
        self.push_screen(
            MoveScreen(lanes=self._lanes),
            callback=lambda lane: self._on_move_result(task, lane),
        )

    # ------------------------------------------------------------------
    # Screen callbacks
    # ------------------------------------------------------------------

    def _on_form_result(self, result: Optional[dict]) -> None:
        if result is None:
            return

        def _do_save() -> None:
            try:
                if result["_mode"] == "create":
                    payload = {
                        "title": result["title"],
                        "content": result["content"],
                        "lane": result["lane"],
                        "tags": result["tags"],
                    }
                    if result.get("due_date"):
                        payload["due_date"] = result["due_date"]
                    api.create_task(self._api_url, payload)
                else:
                    original_title = result.get("_original_title", result["title"])
                    payload = {
                        "content": result["content"],
                        "tags": result["tags"],
                        "due_date": result.get("due_date"),
                    }
                    if result["title"] != original_title:
                        payload["new_title"] = result["title"]
                    api.update_task(self._api_url, original_title, payload)
            except APIError as e:
                self.call_from_thread(self.notify, str(e), severity="error")
                return
            self.call_from_thread(self._reload)

        self.run_worker(_do_save, thread=True)

    def _on_confirm_delete(self, confirmed: bool) -> None:
        if not confirmed:
            return
        task = self._current_task()
        if task is None:
            return

        def _do_delete() -> None:
            try:
                api.delete_task(self._api_url, task["title"])
            except APIError as e:
                self.call_from_thread(self.notify, str(e), severity="error")
                return
            self.call_from_thread(self._reload)

        self.run_worker(_do_delete, thread=True)

    def _on_filter_result(self, result: Optional[dict]) -> None:
        if result is None:
            return
        self._filter = {k: v for k, v in result.items() if v}
        self._reload()

    def _on_move_result(self, task: dict, new_lane: Optional[str]) -> None:
        if new_lane is None:
            return

        def _do_move() -> None:
            try:
                api.move_task(self._api_url, task["title"], new_lane)
            except APIError as e:
                self.call_from_thread(self.notify, str(e), severity="error")
                return
            self.call_from_thread(self._reload)

        self.run_worker(_do_move, thread=True)

    # ------------------------------------------------------------------
    # Focus tracking
    # ------------------------------------------------------------------

    def on_list_view_highlighted(self, _: ListView.Highlighted) -> None:
        """Update focused lane index when a ListView gains a highlight."""
        # Find which LaneColumn contains the currently focused ListView
        cols = self._columns()
        focused = self.focused
        for i, col in enumerate(cols):
            try:
                lv = col.query_one(ListView)
                if lv is focused or lv.has_focus:
                    self._focused_lane_idx = i
                    break
            except Exception:
                pass
