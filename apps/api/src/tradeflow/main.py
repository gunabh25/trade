"""ASGI entrypoint for uvicorn."""

from tradeflow.core.app_factory import create_app

app = create_app()
