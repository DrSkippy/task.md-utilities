FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

COPY ./task_api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# task_lib is a sibling directory; copy it in alongside task_api
COPY ./task_lib /app/task_lib
COPY ./task_api /app/task_api
COPY ./config.yaml /app/config/config.yaml

RUN mkdir -p /data/tasks

EXPOSE 5001

CMD ["gunicorn", "--config", "/app/task_api/gunicorn.conf.py", "task_api.app:create_app()"]
