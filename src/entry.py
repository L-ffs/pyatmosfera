"""Ponto de entrada do Cloudflare Workers (Python)."""
import asgi
from workers import WorkerEntrypoint

from atmosfera.main import create_app

app = create_app()


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        return await asgi.fetch(app, request.js_object, self.env)
