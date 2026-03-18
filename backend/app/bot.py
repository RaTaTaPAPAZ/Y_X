import asyncio
import os

import httpx
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN", "")
API_URL = os.getenv("API_URL", "http://localhost:8000")
WEBAPP_URL = os.getenv("WEBAPP_URL", API_URL)

if not TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN is not configured")

bot = Bot(token=TOKEN)
dp = Dispatcher()


def build_user_headers(message: types.Message) -> dict[str, str]:
    user = message.from_user
    if not user:
        return {}
    headers = {"X-Telegram-Id": str(user.id)}
    if user.username:
        headers["X-Telegram-Username"] = user.username
    if user.first_name:
        headers["X-Telegram-First-Name"] = user.first_name
    if user.last_name:
        headers["X-Telegram-Last-Name"] = user.last_name
    return headers


@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "Yakamy бот готов 🚀\n"
        "Твои данные теперь привязываются к Telegram-аккаунту.\n"
        f"Открой сайт и зайди через Telegram: {WEBAPP_URL}\n\n"
        "Пример: 'создай задачу допилить web страницу, высокий приоритет'"
    )


@dp.message(Command("help"))
async def help_handler(message: types.Message):
    await message.answer(
        "Команды:\n"
        "/start — запуск\n"
        "/help — помощь\n\n"
        "Любое сообщение уйдёт в backend /ai/handle от имени твоего Telegram-аккаунта."
    )


@dp.message()
async def handle_message(message: types.Message):
    text = (message.text or "").strip()
    if not text:
        await message.answer("Пришли текстовое сообщение, чтобы я передал его агенту.")
        return

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{API_URL}/ai/handle",
                json={"text": text},
                headers=build_user_headers(message),
            )
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
            f"\nТвой аккаунт: задач {dashboard.get('tasks', 0)}, заметок {dashboard.get('notes', 0)}, напоминаний {dashboard.get('reminders', 0)}"
        )
    lines.append(f"\nWeb: {WEBAPP_URL}")

    await message.answer("\n".join(lines))


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
