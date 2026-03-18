import json
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.database.models import Note, Reminder, Task
from app.schemas.note import NoteCreate
from app.schemas.reminder import ReminderCreate
from app.schemas.task import TaskCreate
from app.services.note_service import create_note, list_notes
from app.services.reminder_service import create_reminder, list_reminders
from app.services.task_service import create_task, list_tasks

SYSTEM_PROMPT = """
Ты Yakamy — продуктивный AI-агент для Telegram-бота и web-панели.
Твоя задача: понять намерение пользователя и при необходимости вызвать инструмент.
Доступные инструменты работают как MCP-like tools: create_task, create_note, create_reminder, list_tasks, list_notes, list_reminders, get_dashboard.
Если пользователь просит создать сущность — обязательно вызови инструмент.
Если модель не уверена, сначала ответь кратко и предложи следующий шаг.
Возвращай понятный ответ на русском языке.
""".strip()


class OpenClawAgent:
    def __init__(self) -> None:
        self.base_url = os.getenv("OPENCLAW_BASE_URL", "").rstrip("/")
        self.api_key = os.getenv("OPENCLAW_API_KEY", "")
        self.model = os.getenv("OPENCLAW_MODEL", "")
        self.timeout = float(os.getenv("OPENCLAW_TIMEOUT", "30"))

    def is_configured(self) -> bool:
        return bool(self.base_url and self.model)

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _tools(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "create_task",
                    "description": "Создать задачу в БД",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                            "priority": {"type": "string", "enum": ["low", "medium", "high"]},
                        },
                        "required": ["title"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "create_note",
                    "description": "Создать заметку в БД",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                        },
                        "required": ["title"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "create_reminder",
                    "description": "Создать напоминание в БД",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                            "remind_at": {"type": "string", "description": "ISO datetime"},
                        },
                        "required": ["title", "remind_at"],
                    },
                },
            },
            {"type": "function", "function": {"name": "list_tasks", "description": "Получить список задач", "parameters": {"type": "object", "properties": {}}}},
            {"type": "function", "function": {"name": "list_notes", "description": "Получить список заметок", "parameters": {"type": "object", "properties": {}}}},
            {"type": "function", "function": {"name": "list_reminders", "description": "Получить список напоминаний", "parameters": {"type": "object", "properties": {}}}},
            {"type": "function", "function": {"name": "get_dashboard", "description": "Получить общую сводку по системе", "parameters": {"type": "object", "properties": {}}}},
        ]

    def _execute_tool(self, db: Session, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name == "create_task":
            item = create_task(
                db,
                TaskCreate(
                    title=arguments["title"],
                    description=arguments.get("description"),
                    priority=arguments.get("priority", "medium"),
                    source="agent",
                ),
            )
            return {"type": "task", "item": serialize_model(item)}

        if name == "create_note":
            item = create_note(
                db,
                NoteCreate(
                    title=arguments["title"],
                    description=arguments.get("description"),
                    source="agent",
                ),
            )
            return {"type": "note", "item": serialize_model(item)}

        if name == "create_reminder":
            remind_at = parse_datetime(arguments.get("remind_at")) or (datetime.now(timezone.utc) + timedelta(hours=1))
            item = create_reminder(
                db,
                ReminderCreate(
                    title=arguments["title"],
                    description=arguments.get("description"),
                    remind_at=remind_at,
                    source="agent",
                ),
            )
            return {"type": "reminder", "item": serialize_model(item)}

        if name == "list_tasks":
            return {"tasks": [serialize_model(item) for item in list_tasks(db)]}
        if name == "list_notes":
            return {"notes": [serialize_model(item) for item in list_notes(db)]}
        if name == "list_reminders":
            return {"reminders": [serialize_model(item) for item in list_reminders(db)]}
        if name == "get_dashboard":
            return get_dashboard(db)

        raise ValueError(f"Unsupported tool: {name}")

    async def _chat_completion(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> dict[str, Any]:
        payload = {
            "model": self.model,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
            "temperature": 0.2,
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{self.base_url}/v1/chat/completions", headers=self._headers(), json=payload)
            response.raise_for_status()
            return response.json()

    async def run(self, db: Session, user_text: str) -> dict[str, Any]:
        if self.is_configured():
            return await self._run_llm_mode(db, user_text)
        return self._run_fallback_mode(db, user_text)

    async def _run_llm_mode(self, db: Session, user_text: str) -> dict[str, Any]:
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
        ]
        tools = self._tools()
        executed_tools: list[dict[str, Any]] = []

        for _ in range(4):
            data = await self._chat_completion(messages, tools)
            message = data["choices"][0]["message"]
            tool_calls = message.get("tool_calls") or []

            if not tool_calls:
                return {
                    "mode": "openclaw",
                    "reply": message.get("content", "Готово."),
                    "tool_results": executed_tools,
                    "dashboard": get_dashboard(db),
                }

            messages.append(message)
            for tool_call in tool_calls:
                function = tool_call["function"]
                arguments = json.loads(function.get("arguments") or "{}")
                result = self._execute_tool(db, function["name"], arguments)
                executed_tools.append({"tool": function["name"], "result": result})
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "name": function["name"],
                        "content": json.dumps(result, ensure_ascii=False, default=str),
                    }
                )

        return {
            "mode": "openclaw",
            "reply": "Выполнил действия, но остановил цикл tool-calls по лимиту итераций.",
            "tool_results": executed_tools,
            "dashboard": get_dashboard(db),
        }

    def _run_fallback_mode(self, db: Session, user_text: str) -> dict[str, Any]:
        parsed = parse_text(user_text)
        tool_results: list[dict[str, Any]] = []

        if parsed["type"] == "task":
            task = create_task(
                db,
                TaskCreate(
                    title=parsed["title"],
                    description=parsed.get("description"),
                    priority=parsed["priority"],
                    source="fallback-agent",
                ),
            )
            tool_results.append({"tool": "create_task", "result": serialize_model(task)})
            reply = f"Создал задачу: {task.title}"
        elif parsed["type"] == "reminder":
            remind_at = parsed["datetime"] or (datetime.now(timezone.utc) + timedelta(hours=1))
            reminder = create_reminder(
                db,
                ReminderCreate(
                    title=parsed["title"],
                    description=parsed.get("description"),
                    remind_at=remind_at,
                    source="fallback-agent",
                ),
            )
            tool_results.append({"tool": "create_reminder", "result": serialize_model(reminder)})
            reply = f"Создал напоминание: {reminder.title}"
        else:
            note = create_note(
                db,
                NoteCreate(
                    title=parsed["title"],
                    description=parsed.get("description"),
                    source="fallback-agent",
                ),
            )
            tool_results.append({"tool": "create_note", "result": serialize_model(note)})
            reply = f"Сохранил заметку: {note.title}"

        return {
            "mode": "fallback",
            "reply": reply,
            "parsed": {
                **parsed,
                "datetime": parsed["datetime"].isoformat() if parsed.get("datetime") else None,
            },
            "tool_results": tool_results,
            "dashboard": get_dashboard(db),
        }


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.strip()
    try:
        dt = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def parse_text(text: str) -> dict[str, Any]:
    raw_text = text.strip()
    lowered = raw_text.lower()

    result: dict[str, Any] = {
        "type": "note",
        "title": raw_text,
        "description": None,
        "priority": "medium",
        "datetime": None,
    }

    if any(word in lowered for word in ["задач", "task", "todo", "сделай"]):
        result["type"] = "task"
    elif any(word in lowered for word in ["напомин", "remind", "пинг", "alarm"]):
        result["type"] = "reminder"

    if any(word in lowered for word in ["высок", "high", "срочно", "urgent"]):
        result["priority"] = "high"
    elif any(word in lowered for word in ["низк", "low"]):
        result["priority"] = "low"

    if "завтра" in lowered:
        result["datetime"] = datetime.now(timezone.utc) + timedelta(days=1)
    elif "сегодня" in lowered:
        result["datetime"] = datetime.now(timezone.utc) + timedelta(hours=2)

    explicit_dt = re.search(r"(20\d{2}-\d{2}-\d{2}[ t]\d{2}:\d{2})", lowered)
    if explicit_dt:
        result["datetime"] = parse_datetime(explicit_dt.group(1).replace(" ", "T"))

    title = re.sub(r"^(задача|напоминание|заметка)\s*[:\-]?\s*", "", raw_text, flags=re.IGNORECASE).strip()
    result["title"] = title or raw_text
    return result


def serialize_model(instance: Task | Note | Reminder) -> dict[str, Any]:
    data: dict[str, Any] = {}
    for column in instance.__table__.columns:
        value = getattr(instance, column.name)
        data[column.name] = value.isoformat() if isinstance(value, datetime) else value
    return data


def get_dashboard(db: Session) -> dict[str, Any]:
    tasks_total = db.query(Task).count()
    notes_total = db.query(Note).count()
    reminders_total = db.query(Reminder).count()
    return {
        "counts": {
            "tasks": tasks_total,
            "notes": notes_total,
            "reminders": reminders_total,
        },
        "recent_tasks": [serialize_model(item) for item in list_tasks(db)[:5]],
        "recent_notes": [serialize_model(item) for item in list_notes(db)[:5]],
        "upcoming_reminders": [serialize_model(item) for item in list_reminders(db)[:5]],
    }
