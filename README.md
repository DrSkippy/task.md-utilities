# Task.md Utilities (HENDRICKSON KANBAN)

A command-line utility and MCP server for managing tasks organized in lanes, where each task is represented by a markdown file.

## About Tasks.md

This project builds on and extends the [Tasks.md](https://github.com/BaldissaraMatheus/Tasks.md) project. For comprehensive information about the Tasks.md system, including:
- Task visualization and board views
- Core task management concepts
- File format specifications
- VSCode extension and other integrations

Please visit the [Tasks.md repository](https://github.com/BaldissaraMatheus/Tasks.md).

This utilities package provides additional command-line tools and an MCP server interface for programmatic task management.

## Overview

This utility helps manage tasks that are organized in "lanes" (directories). Each task is stored as a markdown file, with the following characteristics:
- Task title is the filename (without .md extension)
- Task content is the file contents
- Tasks can have tags specified using the format `[tag:tagname]`
- Tasks can have due dates specified using the format `[due:YYYY-MM-DD]`
- Tasks can be split into multiple tasks using the `[[split]]` marker
- The system is accessible both via command-line and through an MCP (Model Context Protocol) server

## Installation

**Prerequisites:** Python ≥3.10 and [Poetry](https://python-poetry.org/) must be installed.

1. Clone this repository
2. Install dependencies:
   ```bash
   poetry install
   ```
3. Make the utility executable:
   ```bash
   chmod +x bin/tasks.py
   ```

## Project Structure

```
task.md-utilities/
├── bin/
│   ├── tasks.py          # Main CLI utility
│   └── tag-utility.py    # Tag format conversion utility
├── task_lib/
│   ├── config.py         # Configuration management
│   ├── task.py           # Task model and operations
│   └── task_manager.py   # Task manager with lane operations
├── mcp_task_service/
│   └── server.py         # MCP server for remote task management
├── tests/                # Test suite
└── README.md
```

## Usage

The utility provides several commands to manage tasks:

### Show Tasks
Display all tasks in all lanes:
```bash
./bin/tasks.py --show-tasks
```

Example output:
```
Lane: In Progress
-----------------
Title: Implement login
Tags: frontend, auth
Due Date: 2026-02-01
----------------------------------------
Title: Setup database
Tags: backend, db
----------------------------------------
```

### Add a Lane
Create a new lane (directory) for organizing tasks:
```bash
./bin/tasks.py --add-lane "lane-name"
```

### Split Tasks
Split tasks that contain the `[[split]]` marker into multiple tasks:
```bash
./bin/tasks.py --split-tasks
```
When a task is split:
- The content is divided at each `[[split]]` marker; each segment becomes the body of a new task
- New tasks are named `{n}-{original-title}.md` — e.g., if the original file is `my-feature.md`, the results are `1-my-feature.md`, `2-my-feature.md`, etc.
- The original task is moved to the "Trash" directory
- Tags from the original task are preserved and a `multi-story feature` tag is added

### Create Tasks from CSV
Create multiple tasks from a CSV file:
```bash
./bin/tasks.py --csv-create-tasks path/to/file.csv
```
The CSV file should have these columns:
- `title`: The task title
- `tag_list`: Comma-separated list of tags
- `task`: The task content
- `lane`: The lane to create the task in
- `due_date`: (Optional) Due date in YYYY-MM-DD format

### Change Task Lane
Move a task from its current lane to a new lane:
```bash
./bin/tasks.py --change-lane "task-title" "new-lane-name"
```
This will:
- Search for the task in all lanes
- Create the new lane if it doesn't exist
- Move the task file to the new lane
- Print a message indicating the move was successful

### Empty Trash
Remove all files from the trash directory:
```bash
./bin/tasks.py --empty-trash
```

### Show Statistics Summary
Display statistics about your tasks including lane counts, tasks per lane, and tag usage:
```bash
./bin/tasks.py --summary
```

Example output:
```
==================================================
TASK STATISTICS SUMMARY
==================================================

Total number of lanes: 3

Tasks per lane:
------------------------------
  Backlog: 5 tasks
  Done: 12 tasks
  In Progress: 3 tasks

Tag occurrence counts:
------------------------------
  frontend: 4 occurrences
  urgent: 2 occurrences
  backend: 1 occurrence

Due Date occurrence counts:
------------------------------
  No Due Date: 14 occurrences
  2026-02-15: 6 occurrences
```

### Specify Base Directory
All commands can be run with a different base directory:
```bash
./bin/tasks.py --base-dir /path/to/tasks [other options]
```

If neither `--base-dir` nor a config file is provided, the CLI defaults to the **current working directory**.

## Configuration

The utility can be configured using a JSON configuration file. Use the `--config` option to specify the configuration file:

```bash
./bin/tasks.py --config config.json [other options]
```

When both `--config` and `--base-dir` are provided, `--base-dir` takes precedence over the `base_dir` value in the config file.

### Configuration File Format

```json
{
  "base_dir": "/data/tasks"
}
```

Configuration options:
- `base_dir`: Base directory for tasks (overridden by `--base-dir` on the command line)
- `openai.api_key` / `openai.model`: Reserved for future features; not currently used by any commands

## Task File Format

Each task is stored as a markdown file with the following format:
```markdown
[tag:frontend]
[tag:urgent]
[due:2026-02-15]

Task content goes here...
```

Tags and due dates are optional. They use the following formats:
- Tags: `[tag:tagname]` - One tag per line
- Due dates: `[due:YYYY-MM-DD]` - Must follow ISO date format

## Directory Structure

```
base_directory/
├── Lane1/
│   ├── task1.md
│   └── task2.md
├── Lane2/
│   └── task3.md
└── Trash/
    └── old-task.md
```

## Examples

1. Create a new lane and add tasks:
```bash
./bin/tasks.py --add-lane "In Progress"
```

2. Split a task that contains multiple items:
```markdown
# my-feature.md content:
[tag:project]
[tag:urgent]

First item [[split]] Second item [[split]] Third item
```
After running `--split-tasks`, this creates three new tasks in the same lane:
- `1-my-feature.md` — content: "First item"
- `2-my-feature.md` — content: "Second item"
- `3-my-feature.md` — content: "Third item"

Each split task preserves the original tags and adds a `multi-story feature` tag.

3. Create tasks from a CSV file:
```csv
title,tag_list,task,lane,due_date
"Implement login","frontend, auth","Create login form with validation","In Progress","2026-02-01"
"Setup database","backend, db","Configure PostgreSQL connection","Backlog","2026-02-15"
```

## MCP Server

The HENDRICKSON KANBAN system can be accessed through an MCP (Model Context Protocol) server, allowing AI assistants and other tools to interact with your tasks programmatically.

### Starting the MCP Server

#### Docker Compose (Recommended)

```bash
cd mcp_task_service
docker-compose up -d
```

See [`mcp_task_service/README.md`](mcp_task_service/README.md) for full Docker deployment instructions.

#### Running Locally

```bash
python mcp_task_service/server.py
```

The server will start on `http://0.0.0.0:3003` by default. You can customize the host and port using environment variables:
```bash
HOST=localhost PORT=8080 python mcp_task_service/server.py
```

### MCP Server Configuration

The MCP server looks for a `config.json` file in the current working directory. If not found, it defaults to using `/data/tasks` as the base directory.

### Connecting an MCP Client

To connect Claude Desktop, Claude Code, or Cursor, add the server to your MCP client configuration. The server uses the streamable-HTTP transport at `http://localhost:3003/mcp`.

**Claude Desktop / Claude Code** (`claude_desktop_config.json` or `.mcp.json`):
```json
{
  "mcpServers": {
    "task-manager": {
      "url": "http://localhost:3003/mcp"
    }
  }
}
```

### Available MCP Tools

The MCP server exposes the following tools:

#### 1. add_task_from_json
Add a new task to the system. The entire task definition must be passed as a **JSON string** in the `task_json` parameter:
```json
{
  "task_json": "{\"title\": \"Implement feature X\", \"content\": \"Detailed description\", \"lane\": \"In Progress\", \"tags\": [\"frontend\", \"urgent\"], \"due_date\": \"2026-02-15\"}"
}
```

The JSON string must include:
- `title` (required): Task title
- `content` (required): Task content
- `lane` (required): Lane name
- `tags` (optional): Array of tag strings
- `due_date` (optional): Due date in YYYY-MM-DD format

#### 2. move_task_to_lane
Move a task from its current lane to a new lane.
- **Parameters**: `task_title` (string), `new_lane` (string)

#### 3. list_lanes
List all available lanes and their task counts.

Example response:
```json
{
  "lanes": [
    {"name": "Backlog", "task_count": 5},
    {"name": "In Progress", "task_count": 3},
    {"name": "Done", "task_count": 12}
  ],
  "total_lanes": 3
}
```

#### 4. list_tasks
List tasks with optional filtering.
- **Parameters**: `lane` (optional), `tag` (optional)

Example response:
```json
{
  "tasks": [
    {
      "title": "Implement login",
      "lane": "In Progress",
      "content": "Create login form with validation",
      "tags": ["frontend", "auth"],
      "due_date": "2026-02-01",
      "path": "/data/tasks/In Progress/Implement login.md"
    }
  ],
  "count": 1,
  "filters": {"lane": "In Progress", "tag": null}
}
```

#### 5. update_task
Update a task's properties.
- **Parameters**:
  - `task_title` (required): Current title of the task
  - `content` (optional): New content
  - `tags` (optional): Comma-separated list of new tags
  - `new_title` (optional): New title for the task
  - `due_date` (optional): New due date in YYYY-MM-DD format

#### 6. split_tasks
Split all tasks containing the `[[split]]` marker into multiple subtasks.
- **Returns**: Summary of split operations performed

#### 7. get_statistics
Get comprehensive statistics about tasks.

Example response:
```json
{
  "num_lanes": 3,
  "tasks_per_lane": {"Backlog": 5, "In Progress": 3, "Done": 12},
  "tag_counts": {"frontend": 4, "urgent": 2, "backend": 1},
  "due_date_counts": {"2026-02-15": 6, "No Due Date": 14}
}
```

### Health Check

The MCP server provides a health check endpoint at `/health` for monitoring purposes.

## Utilities

### Tag Format Conversion Utility

The `bin/tag-utility.py` script helps convert tasks from the old tag format (`tags: tag1, tag2, tag3`) to the new format (`[tag:tagname]`).

**Features:**
- Searches for all `.md` files in a directory tree
- Backs up original files with `.bak` extension
- Converts old comma-separated tag format to new bracket format
- Supports dry-run mode to preview changes

**Usage:**
1. Edit the script to set your task directory path
2. Set `dryrun = True` to preview changes; output is printed to stdout. Note: the script also opens a hardcoded output file at `/home/scott/dryrun_output.md` — edit this path before running if needed
3. Set `dryrun = False` to perform the actual conversion (writes output files in-place)
4. Run the script: `python bin/tag-utility.py`

**Note:** This utility is primarily for migrating existing task files to the new format.
