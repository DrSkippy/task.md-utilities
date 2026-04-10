# Task REST API

Flask-based REST API for the HENDRICKSON KANBAN task management system. Exposes all task operations over HTTP so clients (the `tasks` CLI, scripts, other services) can manage tasks from anywhere.

## Endpoints

### Tasks

| Method | Path | Description |
|--------|------|-------------|
| GET | `/tasks` | List tasks (query params: `?lane=`, `?tag=`) |
| POST | `/tasks` | Create a task |
| GET | `/tasks/<title>` | Get a task by title |
| PUT | `/tasks/<title>` | Update task fields |
| DELETE | `/tasks/<title>` | Move task to Trash (soft delete) |
| POST | `/tasks/<title>/move` | Move task to a different lane |

### Lanes

| Method | Path | Description |
|--------|------|-------------|
| GET | `/lanes` | List lanes with task counts |
| POST | `/lanes` | Create a lane |

### Operations

| Method | Path | Description |
|--------|------|-------------|
| POST | `/operations/split` | Split tasks with `[[split]]` marker |
| DELETE | `/operations/trash` | Permanently empty the Trash |
| GET | `/operations/statistics` | Task statistics |

### Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Returns `{"status": "ok"}` |

## Quick Start

### Docker Compose (recommended)

```bash
# From the repo root:
docker build -t localhost:5000/task-api:latest -f task_api/Dockerfile .
docker push localhost:5000/task-api:latest

cd task_api
docker-compose up -d
```

### Running locally (for development)

```bash
pip install -r task_api/requirements.txt
export TASK_CONFIG_PATH=/path/to/config.yaml
gunicorn --config task_api/gunicorn.conf.py "task_api.app:create_app()"
```

## Configuration

The API reads a YAML config file. Provide the path via `TASK_CONFIG_PATH` (default: `/app/config/config.yaml`).

```yaml
# config.yaml
base_dir: /data/tasks
```

Mount this file into the container as a read-only volume (see `docker-compose.yml`). Do **not** bake it into the image.

## Request / Response examples

### Create a task

```bash
curl -X POST http://localhost:2999/tasks \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "Implement login",
    "content": "Create login form with validation",
    "lane": "Backlog",
    "tags": ["frontend", "auth"],
    "due_date": "2026-06-01"
  }'
```

### List tasks filtered by lane

```bash
curl "http://localhost:2999/tasks?lane=Backlog"
```

### Update a task

```bash
curl -X PUT "http://localhost:2999/tasks/Implement%20login" \
  -H 'Content-Type: application/json' \
  -d '{"tags": ["frontend", "auth", "urgent"], "due_date": "2026-05-15"}'
```

### Move a task

```bash
curl -X POST "http://localhost:2999/tasks/Implement%20login/move" \
  -H 'Content-Type: application/json' \
  -d '{"lane": "In Progress"}'
```

## Deployment

Access is provided through NGINX (reverse proxy) and Cloudflare Tunnel. Bind address inside the container is `0.0.0.0:2999`; NGINX handles TLS and routing.
