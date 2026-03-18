import asyncio
from contextlib import asynccontextmanager, suppress
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.bot import bot_runtime_config, start_bot_polling
from app.database.db import Base, engine
from app.routes import agent, auth, notes, reminders, tasks
from app.services.auth_service import telegram_auth_enabled, telegram_bot_username

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
APP_VERSION = "0.4.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    app.state.bot_task = None

    runtime = bot_runtime_config()
    if runtime["bot_enabled"] and runtime["telegram_token_configured"]:
        app.state.bot_task = asyncio.create_task(start_bot_polling())

    try:
        yield
    finally:
        bot_task = getattr(app.state, "bot_task", None)
        if bot_task:
            bot_task.cancel()
            with suppress(asyncio.CancelledError):
                await bot_task


def configure_middleware(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def mount_static(app: FastAPI) -> None:
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def register_routers(app: FastAPI) -> None:
    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    app.include_router(notes.router, prefix="/notes", tags=["notes"])
    app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
    app.include_router(reminders.router, prefix="/reminders", tags=["reminders"])
    app.include_router(agent.router, prefix="/ai", tags=["ai"])


def build_app_info() -> dict[str, Any]:
    runtime = bot_runtime_config()
    return {
        "name": "Yakamy API",
        "version": APP_VERSION,
        "modules": {
            "auth": {
                "telegram_auth_enabled": telegram_auth_enabled(),
                "bot_username": telegram_bot_username(),
            },
            "bot": runtime,
            "agent": {
                "openclaw_base_url_configured": bool(agent.agent.base_url),
                "openclaw_model_configured": bool(agent.agent.model),
            },
            "web": {
                "root": "/",
                "static": "/static",
            },
        },
        "routes": ["/auth/*", "/ai/*", "/tasks/*", "/notes/*", "/reminders/*", "/", "/static/*"],
    }


def create_app() -> FastAPI:
    Base.metadata.create_all(bind=engine)
    app = FastAPI(title="Yakamy API", version=APP_VERSION, lifespan=lifespan)
    configure_middleware(app)
    mount_static(app)
    register_routers(app)

    @app.get("/")
    def root():
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/health")
    def health():
        return {"status": "ok", "version": APP_VERSION}

    @app.get("/app/info")
    def app_info():
        return build_app_info()

    return app


app = create_app()
