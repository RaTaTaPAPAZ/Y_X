from app.database import tasks


def create_task(data: dict):
    task = {
        "id": len(tasks) + 1,
        "title": data.get("title"),
        "description": data.get("description"),
        "status": "todo",
        "priority": data.get("priority", 1)
    }

    tasks.append(task)
    return task