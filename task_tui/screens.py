"""Secondary screens and modals for the kanban TUI."""

from __future__ import annotations

from datetime import date
from typing import Optional

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import (
    Button,
    Input,
    Label,
    ListItem,
    ListView,
    Select,
    TextArea,
)
from textual.containers import Horizontal, Vertical, ScrollableContainer


# ---------------------------------------------------------------------------
# Detail screen
# ---------------------------------------------------------------------------


class DetailScreen(Screen):
    """Read-only full-screen view of a single task."""

    BINDINGS = [
        Binding("escape", "go_back", "Back"),
        Binding("f3", "edit", "Edit"),
        Binding("f4", "delete", "Delete"),
        Binding("f6", "move", "Move"),
        Binding("f7", "go_back", "Detail"),
    ]

    DEFAULT_CSS = """
    DetailScreen {
        layout: vertical;
    }
    DetailScreen > #detail-header {
        background: $accent;
        color: $text;
        text-style: bold;
        padding: 0 1;
        height: 1;
    }
    DetailScreen > #detail-meta {
        background: $surface-darken-1;
        padding: 0 1;
        height: 1;
        color: $text-muted;
    }
    DetailScreen > ScrollableContainer {
        height: 1fr;
        padding: 1 2;
    }
    DetailScreen > #detail-footer {
        dock: bottom;
        height: 1;
        background: $accent-darken-2;
        padding: 0 1;
    }
    """

    def __init__(self, task: dict) -> None:
        # Set instance data BEFORE super().__init__() so compose() can access it
        self._task_data = task
        super().__init__()

    def compose(self) -> ComposeResult:
        t = self._task_data
        tags = ", ".join(t.get("tags") or []) or "—"
        due = t.get("due_date") or "—"
        yield Label(f" {t.get('title', '')}  [Lane: {t.get('lane', '')}]", id="detail-header")
        yield Label(f" Tags: {tags}   Due: {due}", id="detail-meta")
        yield ScrollableContainer(Label(t.get("content", ""), id="detail-content"))
        yield Label("F3 Edit  F4 Delete  F6 Move  F7/Esc Close", id="detail-footer")

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_edit(self) -> None:
        self.app.pop_screen()
        self.app.action_edit_task()  # type: ignore[attr-defined]

    def action_delete(self) -> None:
        self.app.pop_screen()
        self.app.action_delete_task()  # type: ignore[attr-defined]

    def action_move(self) -> None:
        self.app.pop_screen()
        self.app.action_move_task()  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Task form screen (create / edit)
# ---------------------------------------------------------------------------


class TaskFormScreen(Screen):
    """Form screen for creating or editing a task."""

    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    DEFAULT_CSS = """
    TaskFormScreen {
        layout: vertical;
        align: center middle;
    }
    TaskFormScreen > #form-container {
        width: 70;
        height: auto;
        border: round $accent;
        padding: 1 2;
        background: $surface;
    }
    TaskFormScreen Label.field-label {
        margin-top: 1;
        color: $text-muted;
    }
    TaskFormScreen Input, TaskFormScreen TextArea, TaskFormScreen Select {
        width: 100%;
    }
    TaskFormScreen TextArea {
        height: 8;
    }
    TaskFormScreen #form-buttons {
        margin-top: 1;
        height: auto;
        align: right middle;
    }
    TaskFormScreen #error-label {
        color: $error;
        height: auto;
    }
    """

    def __init__(self, task: Optional[dict], lanes: list[str]) -> None:
        # Set instance data BEFORE super().__init__() so compose() can access it
        self._task_data = task
        self._lanes = lanes
        self._mode = "update" if task else "create"
        super().__init__()

    def compose(self) -> ComposeResult:
        t = self._task_data or {}
        title_val = t.get("title", "")
        content_val = t.get("content", "")
        current_lane = t.get("lane", self._lanes[0] if self._lanes else "")
        tags_val = ", ".join(t.get("tags") or [])
        due_val = t.get("due_date") or ""

        lane_options = [(lane, lane) for lane in self._lanes]

        heading = "Edit Task" if self._task_data else "New Task"
        with Vertical(id="form-container"):
            yield Label(heading, id="form-heading")
            yield Label("Title", classes="field-label")
            yield Input(value=title_val, id="input-title", placeholder="Task title")
            yield Label("Content", classes="field-label")
            yield TextArea(content_val, id="input-content")
            yield Label("Lane", classes="field-label")
            yield Select(
                options=lane_options,
                value=current_lane,
                id="input-lane",
            )
            yield Label("Tags (comma-separated)", classes="field-label")
            yield Input(value=tags_val, id="input-tags", placeholder="urgent, backend")
            yield Label("Due Date (YYYY-MM-DD)", classes="field-label")
            yield Input(value=due_val, id="input-due", placeholder="2026-06-01")
            yield Label("", id="error-label")
            with Horizontal(id="form-buttons"):
                yield Button("Cancel", variant="default", id="btn-cancel")
                yield Button("Save", variant="primary", id="btn-save")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel":
            self.dismiss(None)
        elif event.button.id == "btn-save":
            self._save()

    def _save(self) -> None:
        title = self.query_one("#input-title", Input).value.strip()
        content = self.query_one("#input-content", TextArea).text
        lane_select = self.query_one("#input-lane", Select)
        lane = str(lane_select.value) if lane_select.value else ""
        tags_raw = self.query_one("#input-tags", Input).value.strip()
        due_raw = self.query_one("#input-due", Input).value.strip()

        error_label = self.query_one("#error-label", Label)

        if not title:
            error_label.update("Title is required.")
            return

        if due_raw:
            try:
                date.fromisoformat(due_raw)
            except ValueError:
                error_label.update("Due date must be YYYY-MM-DD.")
                return

        tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
        result: dict = {
            "_mode": self._mode,
            "title": title,
            "content": content,
            "lane": lane,
            "tags": tags,
            "due_date": due_raw or None,
        }
        if self._mode == "update" and self._task_data:
            result["_original_title"] = self._task_data["title"]

        self.dismiss(result)

    def action_cancel(self) -> None:
        self.dismiss(None)


# ---------------------------------------------------------------------------
# Confirm screen
# ---------------------------------------------------------------------------


class ConfirmScreen(Screen):
    """Simple yes/no confirmation dialog."""

    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    DEFAULT_CSS = """
    ConfirmScreen {
        align: center middle;
    }
    ConfirmScreen > #confirm-box {
        width: 50;
        height: auto;
        border: round $warning;
        padding: 1 2;
        background: $surface;
    }
    ConfirmScreen #confirm-msg {
        margin-bottom: 1;
    }
    ConfirmScreen #confirm-buttons {
        height: auto;
        align: right middle;
    }
    """

    def __init__(self, message: str) -> None:
        self._message = message
        super().__init__()

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm-box"):
            yield Label(self._message, id="confirm-msg")
            with Horizontal(id="confirm-buttons"):
                yield Button("No", variant="default", id="btn-no")
                yield Button("Yes", variant="error", id="btn-yes")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "btn-yes")

    def action_cancel(self) -> None:
        self.dismiss(False)


# ---------------------------------------------------------------------------
# Filter screen
# ---------------------------------------------------------------------------


class FilterScreen(Screen):
    """Panel for setting lane/tag/string filters."""

    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    DEFAULT_CSS = """
    FilterScreen {
        align: center middle;
    }
    FilterScreen > #filter-box {
        width: 50;
        height: auto;
        border: round $accent;
        padding: 1 2;
        background: $surface;
    }
    FilterScreen Label.field-label {
        margin-top: 1;
        color: $text-muted;
    }
    FilterScreen Input {
        width: 100%;
    }
    FilterScreen #filter-buttons {
        margin-top: 1;
        height: auto;
        align: right middle;
    }
    """

    def __init__(self, current: Optional[dict] = None) -> None:
        self._current = current or {}
        super().__init__()

    def compose(self) -> ComposeResult:
        with Vertical(id="filter-box"):
            yield Label("Filter Tasks", id="filter-heading")
            yield Label("Lane", classes="field-label")
            yield Input(value=self._current.get("lane") or "", id="filter-lane", placeholder="todo")
            yield Label("Tag", classes="field-label")
            yield Input(value=self._current.get("tag") or "", id="filter-tag", placeholder="urgent")
            yield Label("Title contains", classes="field-label")
            yield Input(value=self._current.get("search") or "", id="filter-search", placeholder="login")
            with Horizontal(id="filter-buttons"):
                yield Button("Cancel", variant="default", id="btn-cancel")
                yield Button("Clear", variant="warning", id="btn-clear")
                yield Button("Apply", variant="primary", id="btn-apply")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel":
            self.dismiss(None)
        elif event.button.id == "btn-clear":
            self.dismiss({"lane": None, "tag": None, "search": None})
        elif event.button.id == "btn-apply":
            self.dismiss({
                "lane": self.query_one("#filter-lane", Input).value.strip() or None,
                "tag": self.query_one("#filter-tag", Input).value.strip() or None,
                "search": self.query_one("#filter-search", Input).value.strip() or None,
            })

    def action_cancel(self) -> None:
        self.dismiss(None)


# ---------------------------------------------------------------------------
# Move screen
# ---------------------------------------------------------------------------


class MoveScreen(Screen):
    """Lane picker for moving a task."""

    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    DEFAULT_CSS = """
    MoveScreen {
        align: center middle;
    }
    MoveScreen > #move-box {
        width: 40;
        height: auto;
        max-height: 20;
        border: round $accent;
        padding: 1 2;
        background: $surface;
    }
    MoveScreen ListView {
        height: auto;
        max-height: 15;
    }
    """

    def __init__(self, lanes: list[str]) -> None:
        self._lanes = lanes
        super().__init__()

    def compose(self) -> ComposeResult:
        with Vertical(id="move-box"):
            yield Label("Move to lane:")
            yield ListView(*[ListItem(Label(lane), name=lane) for lane in self._lanes])

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        self.dismiss(event.item.name)

    def action_cancel(self) -> None:
        self.dismiss(None)
