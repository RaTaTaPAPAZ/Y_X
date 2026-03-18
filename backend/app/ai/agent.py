import re
from datetime import datetime, timedelta
from app.services.task_service import create_task
from app.services.reminder_service import create_reminder


def handle_text(text: str):
    parsed = parse_text(text)

    if parsed["type"] == "task":
        return create_task({
            "title": parsed["title"],
            "priority": parsed["priority"]
        })

    elif parsed["type"] == "reminder":
        return create_reminder({
            "title": parsed["title"],
            "remind_at": parsed["datetime"]
        })

    return parsed

def parse_text(text: str):
    text = text.lower()

    result = {
        "type": None,
        "title": text,
        "priority": 1,
        "datetime": None
    }

    # тип
    if "задач" in text:
        result["type"] = "task"
    elif "напомин" in text:
        result["type"] = "reminder"
    else:
        result["type"] = "note"

    # приоритет
    if "высок" in text:
        result["priority"] = 3
    elif "средн" in text:
        result["priority"] = 2

    # дата
    if "завтра" in text:
        result["datetime"] = datetime.now() + timedelta(days=1)

    return result