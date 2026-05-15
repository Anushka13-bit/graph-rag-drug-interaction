"""ASGI entry when running ``uvicorn main:app`` from ``biomedical-graphrag/``."""

from __future__ import annotations

from api.main import app

__all__ = ["app"]
