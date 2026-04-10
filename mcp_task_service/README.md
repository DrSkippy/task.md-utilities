# Task Manager MCP Service

FastMCP server exposing the HENDRICKSON KANBAN task management system over the [Model Context Protocol](https://modelcontextprotocol.io/). AI assistants (Claude, Cursor, etc.) can use this server to read and manage tasks without direct filesystem access.

## Tools

| Tool | Description |
|------|-------------|
| `add_task` | Create a new task with title, content, lane, optional tags and due date |
| `get_task` | Retrieve a single task by title |
| `update_task` | Update task fields (content, tags, title, due date) |
| `delete_task` | Move a task to Trash (soft delete) |
| `move_task_to_lane` | Move a task from one lane to another |
| `list_tasks` | List tasks, optionally filtered by lane and/or tag |
| `list_lanes` | List all lanes with task counts |
| `add_lane` | Create a new lane |
| `split_tasks` | Split tasks containing `[[split]]` into numbered subtasks |
| `empty_trash` | Permanently delete all files in Trash |
| `get_statistics` | Get lane/tag/due-date statistics |

## Quick Start

### Docker Compose (recommended)

```bash
# From the repo root:
docker build -t localhost:5000/task-manager-mcp:latest -f mcp_task_service/Dockerfile .
docker push localhost:5000/task-manager-mcp:latest

cd mcp_task_service
docker-compose up -d
```

The server listens on **port 3003**. The MCP endpoint is at `http://<host>:3003/mcp`.

### Running locally

```bash
pip install -r mcp_task_service/requirements.txt
TASK_CONFIG_PATH=/path/to/config.yaml python mcp_task_service/server.py
```

## Configuration

The server reads a YAML config file. Provide the path via the `TASK_CONFIG_PATH` environment variable (default: `/app/config/config.yaml`).

```yaml
# config.yaml
base_dir: /data/tasks
```

Mount this file into the container as a read-only volume (see `docker-compose.yml`). Do **not** bake config into the image.

### Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TASK_CONFIG_PATH` | `/app/config/config.yaml` | Path to config YAML inside the container |
| `HOST` | `0.0.0.0` | Bind address |
| `PORT` | `3003` | Bind port |

## Connecting an MCP client

Add to your Claude Desktop / Claude Code config (`~/.claude/claude_desktop_config.json` or `.mcp.json`):

```json
{
  "mcpServers": {
    "task-manager": {
      "url": "http://localhost:3003/mcp"
    }
  }
}
```

Replace `localhost` with the server hostname if running remotely (e.g. via NGINX/Cloudflare Tunnel).

## Health check

```bash
curl http://localhost:3003/health
# → OK
```

## Data format

Tasks are stored as `.md` files inside lane subdirectories:

```
base_dir/
├── Backlog/
│   └── My Task.md
├── In Progress/
│   └── Another Task.md
└── Trash/
    └── old-task.md
```

Each file may contain optional metadata at the top:

```markdown
[tag:frontend]
[tag:urgent]
[due:2026-06-01]

Task body text goes here.
```

## Development

To add a new tool, define it in `server.py` with the `@mcp.tool()` decorator:

```python
@mcp.tool()
def my_tool(param: str) -> str:
    """One-line description. Args: param description. Returns: description."""
    ...
```

Keep tool docstrings concise — they are sent to the AI model as part of the tool schema.
