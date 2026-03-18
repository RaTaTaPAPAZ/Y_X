import asyncio
import os

import httpx
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN", "")
API_URL = os.getenv("API_URL", "http://localhost:8000")

if not TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN is not configured")

bot = Bot(token=TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "Yakamy бот готов 🚀\n"
        "Я умею создавать задачи, заметки и напоминания через AI-агента.\n"
        "Пример: 'создай задачу допилить web страницу, высокий приоритет'"
    )


@dp.message(Command("help"))
async def help_handler(message: types.Message):
    await message.answer(
        "Команды:\n"
        "/start — запуск\n"
        "/help — помощь\n\n"
        "Просто напиши сообщение, и я отправлю его в backend /ai/handle."
    )


@dp.message()
async def handle_message(message: types.Message):
    text = (message.text or "").strip()
    if not text:
        await message.answer("Пришли текстовое сообщение, чтобы я передал его агенту.")
        return

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{API_URL}/ai/handle", json={"text": text})
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPError as error:
        await message.answer(f"Backend недоступен: {error}")
        return

    reply = data.get("reply", "Готово")
    tool_results = data.get("tool_results", [])
    dashboard = data.get("dashboard", {}).get("counts", {})

    lines = [f"🤖 {reply}"]
    if tool_results:
        lines.append("\nИнструменты:")
        for item in tool_results:
            lines.append(f"- {item['tool']}")
    if dashboard:
        lines.append(
            f"\nСводка: задач {dashboard.get('tasks', 0)}, заметок {dashboard.get('notes', 0)}, напоминаний {dashboard.get('reminders', 0)}"
        )

    await message.answer("\n".join(lines))


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
