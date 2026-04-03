"""Entry point for running OpenDiscourse as a module."""

from opendiscourse.utils.logging_config import setup_logging

logger = setup_logging()
logger.info("OpenDiscourse starting...")
logger.info("Run with: uvicorn opendiscourse.api.main:app --reload")
