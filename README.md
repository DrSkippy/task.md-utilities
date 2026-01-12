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

1. Clone this repository
2. Make the utility executable:
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
- New tasks are created with names like "1-original-title", "2-original-title", etc.
- The original task is moved to the "Trash" directory
- Tags are preserved in the new tasks

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

### Specify Base Directory
All commands can be run with a different base directory:
```bash
./bin/tasks.py --base-dir /path/to/tasks [other options]
```

## Configuration

The utility can be configured using a JSON configuration file. Use the `--config` option to specify the configuration file:

```bash
./bin/tasks.py --config config.json [other options]
```

### Configuration File Format

```json
{
  "base_dir": "/path/to/tasks",
  "openai": {
    "api_key": "your-api-key-here",
    "model": "gpt-3.5-turbo"
  }
}
```

Configuration options:
- `base_dir`: Base directory for tasks (can be overridden with `--base-dir`)
- `openai.api_key`: OpenAI API key for AI processing (currently reserved for future features)
- `openai.model`: OpenAI model to use (default: "gpt-3.5-turbo")

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
# Original task.md content:
[tag:project]
[tag:urgent]

First item [[split]] Second item [[split]] Third item
```
After running `--split-tasks`, this will create three new tasks:
- `1-original.md`
- `2-original.md`
- `3-original.md`

Each split task will preserve the original tags and add a `multi-story feature` tag.

3. Create tasks from a CSV file:
```csv
title,tag_list,task,lane,due_date
"Implement login","frontend, auth","Create login form with validation","In Progress","2026-02-01"
"Setup database","backend, db","Configure PostgreSQL connection","Backlog","2026-02-15"
```

## MCP Server

The HENDRICKSON KANBAN system can be accessed through an MCP (Model Context Protocol) server, allowing AI assistants and other tools to interact with your tasks programmatically.

### Starting the MCP Server

Run the MCP server using:
```bash
python mcp_task_service/server.py
```

The server will start on `http://0.0.0.0:3003` by default. You can customize the host and port using environment variables:
```bash
HOST=localhost PORT=8080 python mcp_task_service/server.py
```

### MCP Server Configuration

The MCP server looks for a `config.json` file in the current working directory. If not found, it defaults to using `/data/tasks` as the base directory.

### Available MCP Tools

The MCP server exposes the following tools:

#### 1. add_task_from_json
Add a new task to the system.
```json
{
  "title": "Implement feature X",
  "content": "Detailed description of the task",
  "lane": "In Progress",
  "tags": ["frontend", "urgent"],
  "due_date": "2026-02-15"
}
```

#### 2. move_task_to_lane
Move a task from its current lane to a new lane.
- **Parameters**: `task_title` (string), `new_lane` (string)

#### 3. list_lanes
List all available lanes and their task counts.
- **Returns**: JSON with lane names and task counts

#### 4. list_tasks
List tasks with optional filtering.
- **Parameters**: `lane` (optional), `tag` (optional)
- **Returns**: JSON array of tasks with all their properties

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
Get comprehensive statistics about tasks including:
- Number of lanes
- Tasks per lane
- Tag occurrence counts
- Due date distribution

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
2. Set `dryrun = True` to preview changes without modifying files
3. Set `dryrun = False` to perform the actual conversion
4. Run the script: `python bin/tag-utility.py`

**Note:** This utility is primarily for migrating existing task files to the new format.