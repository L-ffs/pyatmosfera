"""Servidor local: `uv run uvicorn dev:app --app-dir src --reload` (serve também a pasta public/)."""
import os

os.environ.setdefault("COOKIE_SECURE", "false")

from atmosfera.main import create_app  # noqa: E402

app = create_app(serve_static=True)
