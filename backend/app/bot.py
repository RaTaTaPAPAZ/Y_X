import asyncio
import os
import httpx
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
API_URL = os.getenv("API_URL")

bot = Bot(token=TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Yakamy бот готов 🚀\nПиши задачу текстом")


@dp.message()
async def handle_message(message: types.Message):
    text = message.text

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_URL}/ai/handle",
            json={"text": text}
        )

    data = response.json()

    await message.answer(f"Создано:\n{data}")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())