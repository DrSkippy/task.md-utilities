#!/usr/bin/env python3
__version__="0.1.0"
__author__="Scott Hendrickson"
__email__="scott@drskippy.net"

"""
FastMCP-based MCP server for task management.
Provides tools for managing tasks using the task_lib library.
"""

import json
import logging
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add parent directory to path to import task_lib
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.server.fastmcp import FastMCP
from task_lib.config import Config
from task_lib.task_manager import TaskManager
from task_lib.task import Task

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastMCP server with streamable HTTP support
port = int(os.getenv("PORT", "3003"))
host = os.getenv("HOST", "0.0.0.0")

# Initialize FastMCP server
mcp = FastMCP("task-manager",
              host=host,
              port=port
              )

# Global task manager instance
task_manager: Optional[TaskManager] = None


def get_task_manager() -> TaskManager:
    """Get or initialize the task manager instance."""
    global task_manager
    if task_manager is None:
        # Try to load config from environment or use default
        config_path = Path.cwd() / "config.json"
        if config_path.exists():
            config = Config(config_path)
        else:
            config = Config()
            # Set default base directory to /data for Docker
            config.base_dir = Path("/data/tasks")
            config.base_dir.mkdir(parents=True, exist_ok=True)

        task_manager = TaskManager(config)
    return task_manager


@mcp.tool()
def add_task_from_json(task_json: str) -> str:
    """
    Add a new task to the HENDRICKSON KANBAN system.

    The HENDRICKSON KANBAN system is a file-based task management system that stores tasks
    as markdown files organized into lanes (workflow stages). Each task is represented by
    a .md file within a lane directory. Tasks can be enriched with tags for categorization
    and due dates for time management. The data store uses a simple directory structure where
    each lane is a subdirectory containing task files, making it easy to version control and
    sync across systems.

    Args:
        task_json: JSON string containing task data with fields:
                  - title (required): Task title
                  - content (required): Task content
                  - lane (required): Lane name
                  - tags (optional): List of tags
                  - due_date (optional): Due date in YYYY-MM-DD format

    Returns:
        Success message or error details
    """
    try:
        task_data = json.loads(task_json)

        # Validate required fields
        if not all(k in task_data for k in ['title', 'content', 'lane']):
            return "Error: Missing required fields (title, content, lane)"

        # Parse due date if provided
        due_date = None
        if 'due_date' in task_data and task_data['due_date']:
            try:
                due_date = datetime.strptime(task_data['due_date'], '%Y-%m-%d')
            except ValueError:
                return f"Error: Invalid due_date format. Use YYYY-MM-DD"

        # Create task
        tm = get_task_manager()
        task = Task(
            title=task_data['title'],
            content=task_data['content'],
            lane=task_data['lane'],
            tags=task_data.get('tags', []),
            due_date=due_date,
            path=tm.base_dir / task_data['lane'] / f"{task_data['title']}.md"
        )

        # Save task to file
        task.to_file(tm.base_dir)

        return f"Successfully created task '{task_data['title']}' in lane '{task_data['lane']}'"

    except json.JSONDecodeError as e:
        return f"Error: Invalid JSON - {str(e)}"
    except Exception as e:
        return f"Error creating task: {str(e)}"


@mcp.tool()
def move_task_to_lane(task_title: str, new_lane: str) -> str:
    """
    Move a task from its current lane to a new lane in the HENDRICKSON KANBAN system.

    The HENDRICKSON KANBAN system is a file-based task management system that stores tasks
    as markdown files organized into lanes (workflow stages). Each task is represented by
    a .md file within a lane directory. Tasks can be enriched with tags for categorization
    and due dates for time management. The data store uses a simple directory structure where
    each lane is a subdirectory containing task files, making it easy to version control and
    sync across systems.

    Args:
        task_title: Title of the task to move
        new_lane: Name of the destination lane

    Returns:
        Success message or error details
    """
    try:
        tm = get_task_manager()

        # Find the task
        all_tasks = tm.get_all_tasks()
        task_found = False
        current_lane = None

        for lane, tasks in all_tasks.items():
            for task in tasks:
                if task.title == task_title:
                    task_found = True
                    current_lane = lane
                    break
            if task_found:
                break

        if not task_found:
            return f"Error: Task '{task_title}' not found in any lane"

        # Use the change_lane method
        tm.change_lane(task_title, new_lane)

        return f"Successfully moved task '{task_title}' from '{current_lane}' to '{new_lane}'"

    except Exception as e:
        return f"Error moving task: {str(e)}"


@mcp.tool()
def list_lanes() -> str:
    """
    List all available lanes in the HENDRICKSON KANBAN system.

    The HENDRICKSON KANBAN system is a file-based task management system that stores tasks
    as markdown files organized into lanes (workflow stages). Each task is represented by
    a .md file within a lane directory. Tasks can be enriched with tags for categorization
    and due dates for time management. The data store uses a simple directory structure where
    each lane is a subdirectory containing task files, making it easy to version control and
    sync across systems.

    Returns:
        JSON string containing list of lane names and task counts
    """
    try:
        tm = get_task_manager()
        all_tasks = tm.get_all_tasks()

        lanes_info = {
            "lanes": [
                {
                    "name": lane,
                    "task_count": len(tasks)
                }
                for lane, tasks in all_tasks.items()
            ],
            "total_lanes": len(all_tasks)
        }

        return json.dumps(lanes_info, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def list_tasks(lane: Optional[str] = None, tag: Optional[str] = None) -> str:
    """
    List tasks from the HENDRICKSON KANBAN system, optionally filtered by lane and/or tag.

    The HENDRICKSON KANBAN system is a file-based task management system that stores tasks
    as markdown files organized into lanes (workflow stages). Each task is represented by
    a .md file within a lane directory. Tasks can be enriched with tags for categorization
    and due dates for time management. The data store uses a simple directory structure where
    each lane is a subdirectory containing task files, making it easy to version control and
    sync across systems.

    Args:
        lane: Optional lane name to filter by
        tag: Optional tag to filter by

    Returns:
        JSON string containing list of tasks with their details
    """
    try:
        tm = get_task_manager()
        all_tasks = tm.get_all_tasks()

        result_tasks = []

        # Filter by lane if specified
        lanes_to_check = {lane: all_tasks[lane]} if lane and lane in all_tasks else all_tasks

        for lane_name, tasks in lanes_to_check.items():
            for task in tasks:
                # Filter by tag if specified
                if tag and (not task.tags or tag not in task.tags):
                    continue

                task_info = {
                    "title": task.title,
                    "lane": task.lane,
                    "content": task.content,
                    "tags": task.tags or [],
                    "due_date": task.due_date.strftime('%Y-%m-%d') if task.due_date else None,
                    "path": str(task.path)
                }
                result_tasks.append(task_info)

        return json.dumps({
            "tasks": result_tasks,
            "count": len(result_tasks),
            "filters": {
                "lane": lane,
                "tag": tag
            }
        }, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def update_task(
        task_title: str,
        content: Optional[str] = None,
        tags: Optional[str] = None,
        new_title: Optional[str] = None,
        due_date: Optional[str] = None
) -> str:
    """
    Update a task's properties in the HENDRICKSON KANBAN system.

    The HENDRICKSON KANBAN system is a file-based task management system that stores tasks
    as markdown files organized into lanes (workflow stages). Each task is represented by
    a .md file within a lane directory. Tasks can be enriched with tags for categorization
    and due dates for time management. The data store uses a simple directory structure where
    each lane is a subdirectory containing task files, making it easy to version control and
    sync across systems.

    Args:
        task_title: Current title of the task to update
        content: New content (optional)
        tags: Comma-separated list of new tags (optional)
        new_title: New title for the task (optional)
        due_date: New due date in YYYY-MM-DD format (optional)

    Returns:
        Success message or error details
    """
    try:
        tm = get_task_manager()

        # Find the task
        all_tasks = tm.get_all_tasks()
        task_to_update = None

        for lane, tasks in all_tasks.items():
            for task in tasks:
                if task.title == task_title:
                    task_to_update = task
                    break
            if task_to_update:
                break

        if not task_to_update:
            return f"Error: Task '{task_title}' not found"

        # Delete old file if title is changing
        old_path = task_to_update.path

        # Update fields
        if content is not None:
            task_to_update.content = content

        if tags is not None:
            task_to_update.tags = [t.strip() for t in tags.split(',') if t.strip()]

        if new_title is not None:
            task_to_update.title = new_title
            task_to_update.path = task_to_update.path.parent / f"{new_title}.md"

        if due_date is not None:
            if due_date:
                try:
                    task_to_update.due_date = datetime.strptime(due_date, '%Y-%m-%d')
                except ValueError:
                    return f"Error: Invalid due_date format. Use YYYY-MM-DD"
            else:
                task_to_update.due_date = None

        # Save updated task
        task_to_update.to_file(tm.base_dir)

        # Remove old file if title changed
        if new_title and old_path.exists():
            old_path.unlink()

        return f"Successfully updated task '{task_to_update.title}'"

    except Exception as e:
        return f"Error updating task: {str(e)}"


@mcp.tool()
def split_tasks() -> str:
    """
    Split all tasks in the HENDRICKSON KANBAN system that contain the [[split]] marker.

    The HENDRICKSON KANBAN system is a file-based task management system that stores tasks
    as markdown files organized into lanes (workflow stages). Each task is represented by
    a .md file within a lane directory. Tasks can be enriched with tags for categorization
    and due dates for time management. The data store uses a simple directory structure where
    each lane is a subdirectory containing task files, making it easy to version control and
    sync across systems.

    Tasks containing [[split]] will be divided at each marker, creating numbered subtasks,
    and the original task will be moved to trash.

    Returns:
        Summary of split operations performed
    """
    try:
        tm = get_task_manager()

        # Get tasks before split
        before_tasks = tm.get_all_tasks()
        tasks_with_split = []

        for lane, tasks in before_tasks.items():
            for task in tasks:
                if '[[split]]' in task.content:
                    tasks_with_split.append(task.title)

        if not tasks_with_split:
            return "No tasks found with [[split]] marker"

        # Perform split
        tm.split_tasks()

        # Get tasks after split
        after_tasks = tm.get_all_tasks()

        return json.dumps({
            "message": "Split operation completed",
            "tasks_split": len(tasks_with_split),
            "original_tasks": tasks_with_split,
            "total_tasks_after": sum(len(tasks) for tasks in after_tasks.values())
        }, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def get_statistics() -> str:
    """
    Get statistics about tasks in the HENDRICKSON KANBAN system.

    The HENDRICKSON KANBAN system is a file-based task management system that stores tasks
    as markdown files organized into lanes (workflow stages). Each task is represented by
    a .md file within a lane directory. Tasks can be enriched with tags for categorization
    and due dates for time management. The data store uses a simple directory structure where
    each lane is a subdirectory containing task files, making it easy to version control and
    sync across systems.

    Returns:
        JSON string containing task statistics including lane counts, tag usage, and due dates
    """
    try:
        tm = get_task_manager()
        stats = tm.calculate_statistics()
        return json.dumps(stats, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    # Run the MCP server
    logging.info("#"*70)
    logging.info("Starting MCP server for HENDRICKSON KANBAN task management")
    logging.info(f"Server version={__version__}")
    logging.info(f"Server created by {__author__}")
    logging.info("#"*70)
    mcp.run(transport="streamable-http")
