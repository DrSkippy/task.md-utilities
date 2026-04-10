"""Custom Textual widgets for the kanban TUI."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widgets import Label, ListItem, ListView, Static


class TaskItem(ListItem):
    """A list item representing a single task."""

    def __init__(self, task: dict) -> None:
        self._task_data = task
        super().__init__()

    @property
    def task(self) -> dict:
        """Return the underlying task dict."""
        return self._task_data

    def compose(self) -> ComposeResult:
        title = self._task_data.get("title", "")
        due = self._task_data.get("due_date")
        tags = self._task_data.get("tags") or []
        badge = f" [{due}]" if due else ""
        tag_str = f" #{' #'.join(tags)}" if tags else ""
        yield Label(f"{title}{tag_str}{badge}")


class LaneColumn(Static):
    """A vertical column for a single kanban lane."""

    DEFAULT_CSS = """
    LaneColumn {
        width: 1fr;
        height: 100%;
        border: round $accent;
        padding: 0;
    }
    LaneColumn > .lane-header {
        background: $accent;
        color: $text;
        text-style: bold;
        text-align: center;
        width: 100%;
        padding: 0 1;
    }
    LaneColumn > ListView {
        height: 1fr;
        background: $surface;
    }
    """

    def __init__(self, lane_name: str, tasks: list[dict]) -> None:
        self._lane_name = lane_name
        self._tasks = tasks
        super().__init__()

    @property
    def lane_name(self) -> str:
        """Return the lane name."""
        return self._lane_name

    @property
    def current_task(self) -> dict | None:
        """Return the currently highlighted task, or None."""
        try:
            lv = self.query_one(ListView)
            child = lv.highlighted_child
            if isinstance(child, TaskItem):
                return child.task
        except Exception:
            pass
        return None

    def compose(self) -> ComposeResult:
        count = len(self._tasks)
        yield Label(f" {self._lane_name} ({count})", classes="lane-header")
        yield ListView(*[TaskItem(t) for t in self._tasks])

    def focus_list(self) -> None:
        """Pass focus into the inner ListView."""
        try:
            self.query_one(ListView).focus()
        except Exception:
            pass


class FunctionKeyBar(Static):
    """Bottom bar displaying available function key actions."""

    DEFAULT_CSS = """
    FunctionKeyBar {
        dock: bottom;
        height: 1;
        background: $accent-darken-2;
        color: $text;
        padding: 0 1;
    }
    """

    # Updated dynamically by the app when context changes
    BOARD_KEYS = "F1 Help  F2 New  F3 Edit  F4 Delete  F5 Filter  F6 Move  F7 Detail  F9 Quit"
    DETAIL_KEYS = "F3 Edit  F4 Delete  F6 Move  F7 Close  Esc Back"

    def __init__(self) -> None:
        super().__init__(self.BOARD_KEYS)

    def set_board_mode(self) -> None:
        """Show board-level key hints."""
        self.update(self.BOARD_KEYS)

    def set_detail_mode(self) -> None:
        """Show detail-level key hints."""
        self.update(self.DETAIL_KEYS)
