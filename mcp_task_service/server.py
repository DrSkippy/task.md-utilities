#!/usr/bin/env python3
"""
FastMCP-based MCP server for the HENDRICKSON KANBAN task management system.

The HENDRICKSON KANBAN system stores tasks as markdown files organized into lane
directories. Each lane is a subdirectory of the task data root; each task is a .md
file named after the task title. Tasks support tags ([tag:name]) and due dates
([due:YYYY-MM-DD]) embedded in the file content.

This server exposes the task management library over the Model Context Protocol so
AI assistants can read and manipulate tasks programmatically.

Configuration:
    TASK_CONFIG_PATH  Path to a YAML config file containing ``base_dir``.
                      Defaults to /app/config/config.yaml.
    HOST              Bind host (default: 0.0.0.0).
    PORT              Bind port (default: 3003).
"""

__version__ = "0.2.0"
__author__ = "Scott Hendrickson"
__email__ = "scott@drskippy.net"

import json
import logging
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List

import yaml
from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import PlainTextResponse

# Add parent directory to path to import task_lib
sys.path.insert(0, str(Path(__file__).parent.parent))

from task_lib.config import Config
from task_lib.task import Task
from task_lib.task_manager import TaskManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("mcp-task-service")

port = int(os.getenv("PORT", "3003"))
host = os.getenv("HOST", "0.0.0.0")

mcp = FastMCP("task-manager", host=host, port=port)

_task_manager: Optional[TaskManager] = None


def get_task_manager() -> TaskManager:
    """Get or initialize the singleton TaskManager instance."""
    global _task_manager
    if _task_manager is None:
        config = Config()
        config_path = Path(os.getenv("TASK_CONFIG_PATH", "/app/config/config.yaml"))
        if config_path.exists():
            data = yaml.safe_load(config_path.read_text())
            config.base_dir = Path(data["base_dir"])
            logger.info(f"Loaded config from {config_path}: base_dir={config.base_dir}")
        else:
            config.base_dir = Path("/data/tasks")
            logger.info(f"No config file found at {config_path}, using default base_dir={config.base_dir}")
        config.base_dir.mkdir(parents=True, exist_ok=True)
        _task_manager = TaskManager(config)
    return _task_manager


def _task_to_dict(task: Task) -> dict:
    return {
        "title": task.title,
        "lane": task.lane,
        "content": task.content,
        "tags": task.tags or [],
        "due_date": task.due_date.strftime("%Y-%m-%d") if task.due_date else None,
        "path": str(task.path),
    }


def _find_task(tm: TaskManager, title: str) -> Optional[Task]:
    """Search all lanes for a task with the given title (case-insensitive)."""
    title_lower = title.lower()
    for tasks in tm.get_all_tasks().values():
        for task in tasks:
            if task.title.lower() == title_lower:
                return task
    return None


@mcp.tool()
def add_task(
    title: str,
    content: str,
    lane: str,
    tags: Optional[List[str]] = None,
    due_date: Optional[str] = None,
) -> str:
    """
    Add a new task to the kanban board.

    Args:
        title: Task title (becomes the filename, without .md extension).
        content: Task body text (plain text or markdown).
        lane: Target lane name. The lane directory will be created if it does not exist.
        tags: Optional list of tag strings for categorisation.
        due_date: Optional due date in YYYY-MM-DD format.

    Returns:
        Confirmation message or error description.
    """
    try:
        parsed_due: Optional[datetime] = None
        if due_date:
            try:
                parsed_due = datetime.strptime(due_date, "%Y-%m-%d")
            except ValueError:
                return f"Error: Invalid due_date '{due_date}'. Use YYYY-MM-DD format."

        tm = get_task_manager()
        task = Task(
            title=title,
            content=content,
            lane=lane,
            tags=tags or [],
            due_date=parsed_due,
            path=tm.base_dir / lane / f"{title}.md",
        )
        task.to_file(tm.base_dir)
        return f"Successfully created task '{title}' in lane '{lane}'"
    except Exception as e:
        return f"Error creating task: {e}"


@mcp.tool()
def get_task(title: str) -> str:
    """
    Retrieve a single task by its title, searching across all lanes.

    Args:
        title: Exact task title (case-sensitive, no .md extension).

    Returns:
        JSON object with task details, or an error message if not found.
    """
    try:
        tm = get_task_manager()
        task = _find_task(tm, title)
        if task is None:
            return json.dumps({"error": f"Task '{title}' not found in any lane"})
        return json.dumps(_task_to_dict(task), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def move_task_to_lane(task_title: str, new_lane: str) -> str:
    """
    Move a task from its current lane to a different lane.

    Args:
        task_title: Title of the task to move.
        new_lane: Name of the destination lane (created if it does not exist).

    Returns:
        Confirmation message or error description.
    """
    try:
        tm = get_task_manager()
        task = _find_task(tm, task_title)
        if task is None:
            return f"Error: Task '{task_title}' not found in any lane"
        current_lane = task.lane
        tm.change_lane(task_title, new_lane)
        return f"Successfully moved task '{task_title}' from '{current_lane}' to '{new_lane}'"
    except Exception as e:
        return f"Error moving task: {e}"


@mcp.tool()
def delete_task(title: str) -> str:
    """
    Move a task to the Trash directory (soft delete).

    Args:
        title: Exact task title to delete.

    Returns:
        Confirmation message or error description.
    """
    try:
        tm = get_task_manager()
        task = _find_task(tm, title)
        if task is None:
            return f"Error: Task '{title}' not found in any lane"
        trash_path = tm.trash_dir / task.path.name
        shutil.move(str(task.path), str(trash_path))
        return f"Moved task '{title}' to Trash"
    except Exception as e:
        return f"Error deleting task: {e}"


@mcp.tool()
def list_lanes() -> str:
    """
    List all available lanes with their task counts.

    Returns:
        JSON object with a ``lanes`` array (name, task_count) and ``total_lanes``.
    """
    try:
        tm = get_task_manager()
        all_tasks = tm.get_all_tasks()
        return json.dumps(
            {
                "lanes": [
                    {"name": lane, "task_count": len(tasks)}
                    for lane, tasks in all_tasks.items()
                ],
                "total_lanes": len(all_tasks),
            },
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def add_lane(lane_name: str) -> str:
    """
    Create a new lane (workflow stage directory) in the kanban board.

    Args:
        lane_name: Name for the new lane. Must be a valid directory name.

    Returns:
        Confirmation message or error description.
    """
    try:
        tm = get_task_manager()
        tm.add_lane(lane_name)
        return f"Successfully created lane '{lane_name}'"
    except Exception as e:
        return f"Error creating lane: {e}"


@mcp.tool()
def list_tasks(lane: Optional[str] = None, tag: Optional[str] = None) -> str:
    """
    List tasks, optionally filtered by lane and/or tag.

    Args:
        lane: If provided, return only tasks in this lane.
        tag: If provided, return only tasks that have this tag.

    Returns:
        JSON object with a ``tasks`` array, ``count``, and active ``filters``.
    """
    try:
        tm = get_task_manager()
        all_tasks = tm.get_all_tasks()

        if lane:
            lane_lower = lane.lower()
            lanes_to_check = {k: v for k, v in all_tasks.items() if k.lower() == lane_lower}
        else:
            lanes_to_check = all_tasks

        result = []
        for tasks in lanes_to_check.values():
            for task in tasks:
                if tag and (not task.tags or tag.lower() not in [t.lower() for t in task.tags]):
                    continue
                result.append(_task_to_dict(task))

        return json.dumps(
            {"tasks": result, "count": len(result), "filters": {"lane": lane, "tag": tag}},
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def update_task(
    task_title: str,
    content: Optional[str] = None,
    tags: Optional[List[str]] = None,
    new_title: Optional[str] = None,
    due_date: Optional[str] = None,
) -> str:
    """
    Update one or more fields of an existing task.

    Only the fields you provide will be changed; omitted fields are left as-is.
    To clear the due date, pass an empty string for ``due_date``.

    Args:
        task_title: Current title of the task to update.
        content: New body text (optional).
        tags: New list of tags, replacing all existing tags (optional).
        new_title: Rename the task to this title (optional).
        due_date: New due date in YYYY-MM-DD format, or empty string to clear (optional).

    Returns:
        Confirmation message or error description.
    """
    try:
        tm = get_task_manager()
        task = _find_task(tm, task_title)
        if task is None:
            return f"Error: Task '{task_title}' not found"

        old_path = task.path

        if content is not None:
            task.content = content

        if tags is not None:
            task.tags = tags

        if new_title is not None:
            task.title = new_title
            task.path = task.path.parent / f"{new_title}.md"

        if due_date is not None:
            if due_date:
                try:
                    task.due_date = datetime.strptime(due_date, "%Y-%m-%d")
                except ValueError:
                    return f"Error: Invalid due_date '{due_date}'. Use YYYY-MM-DD format."
            else:
                task.due_date = None

        task.to_file(tm.base_dir)

        if new_title and old_path.exists():
            old_path.unlink()

        return f"Successfully updated task '{task.title}'"
    except Exception as e:
        return f"Error updating task: {e}"


@mcp.tool()
def split_tasks() -> str:
    """
    Split all tasks that contain the ``[[split]]`` marker into numbered subtasks.

    Tasks are divided at each ``[[split]]`` occurrence; each segment becomes a new
    task named ``{n}-{original-title}``. Original tags are preserved and a
    ``multi-story feature`` tag is added. The original task is moved to Trash.

    Returns:
        JSON summary of the split operation.
    """
    try:
        tm = get_task_manager()
        before = tm.get_all_tasks()
        tasks_with_split = [
            task.title
            for tasks in before.values()
            for task in tasks
            if "[[split]]" in task.content
        ]

        if not tasks_with_split:
            return "No tasks found with [[split]] marker"

        tm.split_tasks()
        after = tm.get_all_tasks()

        return json.dumps(
            {
                "message": "Split operation completed",
                "tasks_split": len(tasks_with_split),
                "original_tasks": tasks_with_split,
                "total_tasks_after": sum(len(t) for t in after.values()),
            },
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def empty_trash() -> str:
    """
    Permanently delete all files in the Trash directory.

    Returns:
        Confirmation message with the number of files removed.
    """
    try:
        tm = get_task_manager()
        tm.empty_trash()
        return "Trash emptied successfully"
    except Exception as e:
        return f"Error emptying trash: {e}"


@mcp.tool()
def get_statistics() -> str:
    """
    Get statistics about the kanban board.

    Returns:
        JSON object with ``num_lanes``, ``tasks_per_lane``, ``tag_counts``, and
        ``due_date_counts``.
    """
    try:
        tm = get_task_manager()
        stats = tm.calculate_statistics()
        return json.dumps(stats, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> PlainTextResponse:
    return PlainTextResponse("OK")


if __name__ == "__main__":
    logger.info("#" * 70)
    logger.info("Starting MCP server for HENDRICKSON KANBAN task management")
    logger.info(f"Server version={__version__}")
    logger.info(f"Server created by {__author__}")
    logger.info("#" * 70)
    mcp.run(transport="streamable-http")
