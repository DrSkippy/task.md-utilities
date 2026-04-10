"""Bulk operation endpoints: split, trash, statistics."""

from flask import Blueprint, current_app, jsonify
from task_api.models import MessageResponse, SplitResponse, StatisticsResponse
from task_lib.task_manager import TaskManager

ops_bp = Blueprint("operations", __name__)


def _get_tm() -> TaskManager:
    return current_app.config["TASK_MANAGER"]


@ops_bp.route("/split", methods=["POST"])
def split_tasks():
    """Split all tasks containing the ``[[split]]`` marker into numbered subtasks."""
    tm = _get_tm()
    before = tm.get_all_tasks()
    tasks_with_split = [
        task.title
        for tasks in before.values()
        for task in tasks
        if "[[split]]" in task.content
    ]

    if not tasks_with_split:
        return jsonify(MessageResponse(message="No tasks found with [[split]] marker").model_dump()), 200

    tm.split_tasks()
    after = tm.get_all_tasks()

    response = SplitResponse(
        message="Split operation completed",
        tasks_split=len(tasks_with_split),
        original_tasks=tasks_with_split,
        total_tasks_after=sum(len(t) for t in after.values()),
    )
    return jsonify(response.model_dump()), 200


@ops_bp.route("/statistics", methods=["GET"])
def get_statistics():
    """Return lane/tag/due-date statistics."""
    tm = _get_tm()
    stats = tm.calculate_statistics()
    response = StatisticsResponse(**stats)
    return jsonify(response.model_dump()), 200


@ops_bp.route("/trash", methods=["DELETE"])
def empty_trash():
    """Permanently delete all files in the Trash directory."""
    tm = _get_tm()
    tm.empty_trash()
    return jsonify(MessageResponse(message="Trash emptied").model_dump()), 200
