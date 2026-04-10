"""Lane management endpoints."""

from flask import Blueprint, current_app, jsonify, request
from task_api.models import ErrorResponse, LaneInfo, LanesResponse, MessageResponse
from task_lib.task_manager import TaskManager

lanes_bp = Blueprint("lanes", __name__)


def _get_tm() -> TaskManager:
    return current_app.config["TASK_MANAGER"]


@lanes_bp.route("", methods=["GET"])
def list_lanes():
    """List all lanes with their task counts."""
    tm = _get_tm()
    all_tasks = tm.get_all_tasks()
    response = LanesResponse(
        lanes=[LaneInfo(name=lane, task_count=len(tasks)) for lane, tasks in all_tasks.items()],
        total_lanes=len(all_tasks),
    )
    return jsonify(response.model_dump()), 200


@lanes_bp.route("", methods=["POST"])
def create_lane():
    """Create a new lane. Body: ``{"name": "lane-name"}``."""
    body = request.get_json(force=True) or {}
    name = body.get("name")
    if not name:
        return jsonify(ErrorResponse(error="Missing required field: name").model_dump()), 422

    tm = _get_tm()
    tm.add_lane(name)
    return jsonify(MessageResponse(message=f"Created lane '{name}'").model_dump()), 201
