"""Cria a aplicação FastAPI e liga os routers."""
from pathlib import Path

from fastapi import FastAPI

from .boundary.auth_router import AuthRouter
from .boundary.city_router import CityRouter
from .boundary.error_handlers import register_error_handlers
from .boundary.weather_router import WeatherRouter


def create_app(serve_static: bool = False, public_dir: Path | None = None) -> FastAPI:
    """`serve_static=True` serve a pasta public/ (só no desenvolvimento local;
    no Cloudflare os arquivos estáticos são servidos pela própria plataforma)."""
    app = FastAPI(title="Atmosfera", docs_url=None, redoc_url=None, openapi_url=None)
    register_error_handlers(app)
    for router in (AuthRouter(), CityRouter(), WeatherRouter()):
        app.include_router(router.router)

    if serve_static:
        from fastapi.responses import FileResponse
        from fastapi.staticfiles import StaticFiles

        folder = public_dir or Path(__file__).resolve().parents[2] / "public"

        @app.get("/signup", include_in_schema=False)
        async def signup_page():
            return FileResponse(folder / "signup.html")

        @app.get("/home", include_in_schema=False)
        async def home_page():
            return FileResponse(folder / "home.html")

        app.mount("/", StaticFiles(directory=folder, html=True), name="public")
    return app
