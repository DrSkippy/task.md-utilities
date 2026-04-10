"""Gunicorn configuration for the Task REST API."""

bind = "0.0.0.0:2999"
workers = 2
worker_class = "sync"
timeout = 30
accesslog = "-"
errorlog = "-"
loglevel = "info"
