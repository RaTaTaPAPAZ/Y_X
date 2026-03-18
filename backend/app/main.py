from fastapi import FastAPI

from app.routes import notes, tasks, reminders
from app.routes import agent
app = FastAPI()

app.include_router(notes.router, prefix="/notes", tags=["notes"])
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
app.include_router(reminders.router, prefix="/reminders", tags=["reminders"])
app.include_router(agent.router, prefix="/ai", tags=["ai"])

@app.get("/")
def root():
    return {"message": "Yakamy API работает"}