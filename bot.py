import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import CommandStart
from aiogram.types import Message

# Tokenni environment variable'dan o'qiymiz (Render -> Environment -> BOT_TOKEN)
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError(
        "BOT_TOKEN topilmadi! Render dashboard -> Environment bo'limiga "
        "BOT_TOKEN nomi bilan tokeningizni qo'shing."
    )

logging.basicConfig(level=logging.INFO)

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("Salom! Bot ishlayapti ✅")


@router.message()
async def echo_handler(message: Message):
    await message.answer(f"Siz yozdingiz: {message.text}")


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())