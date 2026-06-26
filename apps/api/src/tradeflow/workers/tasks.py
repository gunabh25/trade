from tradeflow.core.logging import get_logger
from tradeflow.workers.celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task(name="tradeflow.workers.tasks.ping")
def ping() -> dict[str, str]:
    """Connectivity task used to verify Celery worker health."""
    logger.info("celery_ping")
    return {"status": "pong"}
