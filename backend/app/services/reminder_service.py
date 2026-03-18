from app.database import reminders


def create_reminder(data: dict):
    reminder = {
        "id": len(reminders) + 1,
        "title": data.get("title"),
        "remind_at": data.get("remind_at")
    }

    reminders.append(reminder)
    return reminder