"""Task CRUD endpoints."""

import shutil
from datetime import datetime
from typing import Optional

from flask import Blueprint, current_app, jsonify, request
from pydantic import ValidationError

from task_api.models import (
    ErrorResponse,
    MessageResponse,
    TaskCreate,
    TaskResponse,
    TaskUpdate,
)
from task_lib.task import Task
from task_lib.task_manager import TaskManager

tasks_bp = Blueprint("tasks", __name__)


def _get_tm() -> TaskManager:
    return current_app.config["TASK_MANAGER"]


def _task_to_response(task: Task) -> dict:
    return TaskResponse(
        title=task.title,
        content=task.content,
        lane=task.lane,
        tags=task.tags or [],
        due_date=task.due_date.strftime("%Y-%m-%d") if task.due_date else None,
        path=str(task.path),
    ).model_dump()


def _find_task(tm: TaskManager, title: str) -> Optional[Task]:
    """Find a task by title (case-insensitive)."""
    title_lower = title.lower()
    for tasks in tm.get_all_tasks().values():
        for task in tasks:
            if task.title.lower() == title_lower:
                return task
    return None


@tasks_bp.route("", methods=["GET"])
def list_tasks():
    """List tasks, optionally filtered by ``?lane=``, ``?tag=``, and/or ``?search=``."""
    lane = request.args.get("lane")
    tag = request.args.get("tag")
    search = request.args.get("search")

    tm = _get_tm()
    all_tasks = tm.get_all_tasks()

    # Lane filter is case-insensitive
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
            if search and search.lower() not in task.title.lower():
                continue
            result.append(_task_to_response(task))

    result.sort(key=lambda t: (t["lane"], t["title"]))
    return jsonify(result), 200


@tasks_bp.route("", methods=["POST"])
def create_task():
    """Create a new task."""
    try:
        payload = TaskCreate.model_validate(request.get_json(force=True))
    except ValidationError as e:
        return jsonify(ErrorResponse(error="Validation failed", detail=str(e)).model_dump()), 422

    tm = _get_tm()
    due_date = (
        datetime(payload.due_date.year, payload.due_date.month, payload.due_date.day)
        if payload.due_date
        else None
    )
    task = Task(
        title=payload.title,
        content=payload.content,
        lane=payload.lane,
        tags=payload.tags,
        due_date=due_date,
        path=tm.base_dir / payload.lane / f"{payload.title}.md",
    )
    task.to_file(tm.base_dir)
    return jsonify(_task_to_response(task)), 201


@tasks_bp.route("/<path:title>", methods=["GET"])
def get_task(title: str):
    """Retrieve a single task by title."""
    tm = _get_tm()
    task = _find_task(tm, title)
    if task is None:
        return jsonify(ErrorResponse(error=f"Task '{title}' not found").model_dump()), 404
    return jsonify(_task_to_response(task)), 200


@tasks_bp.route("/<path:title>", methods=["PUT"])
def update_task(title: str):
    """Update one or more fields of an existing task."""
    try:
        payload = TaskUpdate.model_validate(request.get_json(force=True))
    except ValidationError as e:
        return jsonify(ErrorResponse(error="Validation failed", detail=str(e)).model_dump()), 422

    tm = _get_tm()
    task = _find_task(tm, title)
    if task is None:
        return jsonify(ErrorResponse(error=f"Task '{title}' not found").model_dump()), 404

    old_path = task.path
    changed = payload.model_fields_set

    if "content" in changed and payload.content is not None:
        task.content = payload.content

    if "tags" in changed and payload.tags is not None:
        task.tags = payload.tags

    if "new_title" in changed and payload.new_title is not None:
        task.title = payload.new_title
        task.path = task.path.parent / f"{payload.new_title}.md"

    if "due_date" in changed:
        if payload.due_date is not None:
            task.due_date = datetime(
                payload.due_date.year, payload.due_date.month, payload.due_date.day
            )
        else:
            task.due_date = None

    task.to_file(tm.base_dir)

    if "new_title" in changed and payload.new_title and old_path.exists():
        old_path.unlink()

    return jsonify(_task_to_response(task)), 200


@tasks_bp.route("/<path:title>", methods=["DELETE"])
def delete_task(title: str):
    """Move a task to Trash (soft delete)."""
    tm = _get_tm()
    task = _find_task(tm, title)
    if task is None:
        return jsonify(ErrorResponse(error=f"Task '{title}' not found").model_dump()), 404

    trash_path = tm.trash_dir / task.path.name
    shutil.move(str(task.path), str(trash_path))
    return "", 204


@tasks_bp.route("/<path:title>/move", methods=["POST"])
def move_task(title: str):
    """Move a task to a different lane. Body: ``{"lane": "new-lane"}``."""
    body = request.get_json(force=True) or {}
    new_lane = body.get("lane")
    if not new_lane:
        return jsonify(ErrorResponse(error="Missing required field: lane").model_dump()), 422

    tm = _get_tm()
    task = _find_task(tm, title)
    if task is None:
        return jsonify(ErrorResponse(error=f"Task '{title}' not found").model_dump()), 404

    old_lane = task.lane
    tm.change_lane(title, new_lane)
    return jsonify(MessageResponse(message=f"Moved '{title}' from '{old_lane}' to '{new_lane}'").model_dump()), 200
