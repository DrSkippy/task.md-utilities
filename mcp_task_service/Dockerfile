FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY ./mcp_task_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy task_lib from parent directory
COPY ./task_lib /app/task_lib

# Copy server code
COPY ./mcp_task_service/server.py .

# Create data directory for tasks
RUN mkdir -p /data/tasks

# Expose port
EXPOSE 3003

# Make server executable
RUN chmod +x server.py

# Run the MCP server
CMD ["python", "server.py"]
