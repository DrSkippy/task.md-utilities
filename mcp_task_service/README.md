# Task Manager MCP Service

A FastMCP-based Model Context Protocol (MCP) server for managing tasks using the task.md format.

## Features

The service provides the following tools:

- **add_task_from_json**: Create a new task from JSON data
- **move_task_to_lane**: Move a task between lanes
- **list_lanes**: List all available lanes with task counts
- **list_tasks**: List tasks with optional filtering by lane and/or tag
- **update_task**: Update task properties (content, tags, title, due date)
- **split_tasks**: Split tasks containing `[[split]]` marker into multiple tasks
- **get_statistics**: Get statistics about tasks (lane counts, tag usage, due dates)

## Quick Start

### Using Docker Compose (Recommended)

1. Build and start the service:
```bash
cd mcp_task_service
docker-compose up -d
```

2. The service will be available on port 3003

3. Stop the service:
```bash
docker-compose down
```

### Using Docker Directly

1. Build the image:
```bash
docker build -t task-manager-mcp -f mcp_task_service/Dockerfile .
```

```bash
docker build -t localhost:5000/task-manager-mcp:latest -f mcp_task_service/Dockerfile .
docker push localhost:5000/task-manager-mcp:latest
```

2. Run the container:
```bash
docker run -d \
  -p 3003:3003 \
  -v $(pwd)/test_tasks:/data/tasks \
  --name task-manager-mcp \
  task-manager-mcp
```

### Running Locally

1. Install dependencies:
```bash
cd mcp_task_service
pip install -r requirements.txt
```

2. Run the server:
```bash
python server.py
```

## Configuration

### Custom Configuration File

Create a `config.json` file in the `mcp_task_service` directory:

```json
{
  "base_dir": "/data/tasks"
}
```

## Tool Usage Examples

### add_task_from_json

```json
{
  "task_json": "{\"title\": \"Example Task\", \"content\": \"Task description\", \"lane\": \"todo\", \"tags\": [\"urgent\", \"bug\"], \"due_date\": \"2025-12-31\"}"
}
```

### move_task_to_lane

```json
{
  "task_title": "Example Task",
  "new_lane": "doing"
}
```

### list_tasks

```json
{
  "lane": "todo",
  "tag": "urgent"
}
```

### update_task

```json
{
  "task_title": "Example Task",
  "content": "Updated content",
  "tags": "urgent,feature",
  "new_title": "Renamed Task",
  "due_date": "2026-01-15"
}
```

### split_tasks

No parameters required. Splits all tasks containing `[[split]]` marker.

## Data Persistence

Task data is stored in the `./data` directory (or `/data/tasks` inside the container). This directory is mounted as a volume to persist data between container restarts.

## Architecture

- **FastMCP**: Provides the MCP server framework
- **task_lib**: Core task management library
- **Docker**: Containerization for easy deployment
- **Port 3003**: Default exposed port for MCP communication

## Development

### Project Structure

```
mcp_task_service/
├── server.py           # FastMCP server implementation
├── Dockerfile          # Docker image definition
├── docker-compose.yml  # Docker Compose configuration
├── requirements.txt    # Python dependencies
├── README.md          # This file
├── config.json        # Optional configuration file
└── data/              # Task data storage (created on first run)
```

### Adding New Tools

To add new tools, define them in `server.py` using the `@mcp.tool()` decorator:

```python
@mcp.tool()
def my_new_tool(param1: str, param2: int) -> str:
    """Tool description"""
    # Implementation
    return "result"
```

## Troubleshooting

### Container won't start

Check logs:
```bash
docker-compose logs -f task-manager-mcp
```

### Permission issues with data directory

Ensure the data directory has correct permissions:
```bash
chmod -R 755 mcp_task_service/data
```

### Port 3003 already in use

Change the port mapping in `docker-compose.yml`:
```yaml
ports:
  - "3004:3003"  # Use port 3004 instead
```

## License

Same as parent project.
