# Task.md Utilities

A command-line utility for managing tasks organized in lanes, where each task is represented by a markdown file.

## Overview

This utility helps manage tasks that are organized in "lanes" (directories). Each task is stored as a markdown file, with the following characteristics:
- Task title is the filename (without .md extension)
- Task content is the file contents
- Tasks can have tags specified in a single line starting with "tags:"
- Tasks can be split into multiple tasks using the `[[split]]` marker

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
│   └── task-util.py
├── task_lib/
│   ├── task.py
│   └── task_manager.py
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
- `openai.api_key`: OpenAI API key for AI processing
- `openai.model`: OpenAI model to use (default: "gpt-3.5-turbo")

### Command Line Options

## Task File Format

Each task is stored as a markdown file with the following format:
```markdown
tags: tag1, tag2, tag3

Task content goes here...
```

The tags line is optional. If present, it must be the first line of the file.

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
tags: project, urgent

First item [[split]] Second item [[split]] Third item
```
After running `--split-tasks`, this will create three new tasks:
- `1-original.md`
- `2-original.md`
- `3-original.md`

3. Create tasks from a CSV file:
```csv
title,tag_list,task,lane
"Implement login","frontend, auth","Create login form with validation","In Progress"
"Setup database","backend, db","Configure PostgreSQL connection","Backlog"
```
