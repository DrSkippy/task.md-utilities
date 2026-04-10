"""Flask application factory for the Task REST API."""

import logging
import sys
from pathlib import Path

from flask import Flask

# Allow importing task_lib when running outside of the installed package
sys.path.insert(0, str(Path(__file__).parent.parent))

from task_api.config import ApiConfig
from task_api.routes.health import health_bp
from task_api.routes.lanes import lanes_bp
from task_api.routes.operations import ops_bp
from task_api.routes.tasks import tasks_bp
from task_lib.config import Config
from task_lib.task_manager import TaskManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("task-api")


def create_app() -> Flask:
    """Create and configure the Flask application.

    Reads task data location from the YAML config file (path given by
    ``TASK_CONFIG_PATH`` env var). Registers all blueprints and attaches a
    shared ``TaskManager`` instance to ``app.config``.
    """
    app = Flask(__name__)

    api_cfg = ApiConfig()

    lib_cfg = Config()
    lib_cfg.base_dir = api_cfg.base_dir
    lib_cfg.base_dir.mkdir(parents=True, exist_ok=True)

    app.config["TASK_MANAGER"] = TaskManager(lib_cfg)
    logger.info(f"Task API started — base_dir={api_cfg.base_dir}")

    app.register_blueprint(health_bp)
    app.register_blueprint(tasks_bp, url_prefix="/tasks")
    app.register_blueprint(lanes_bp, url_prefix="/lanes")
    app.register_blueprint(ops_bp, url_prefix="/operations")

    return app
