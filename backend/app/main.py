from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.database.db import Base, engine
from app.routes import agent, notes, reminders, tasks

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Yakamy API", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.include_router(notes.router, prefix="/notes", tags=["notes"])
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
app.include_router(reminders.router, prefix="/reminders", tags=["reminders"])
app.include_router(agent.router, prefix="/ai", tags=["ai"])


@app.get("/")
def root():
    return FileResponse(static_dir / "index.html")
