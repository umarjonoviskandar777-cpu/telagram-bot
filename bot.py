import asyncio
import logging
import sys
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
import yt_dlp

TOKEN = "8297785685:AAHjhwZVXjenWqy7qCpxeyawV2jsDLQEn5U"

dp = Dispatcher()

@dp.message(CommandStart())
async def command_start_handler(message: types.Message):
    await message.answer("Salom! Menga YouTube, Instagram, TikTok, Facebook yoki Likee tarmoqlaridan video havolasini yuboring, uni yuklab beraman.")

@dp.message()
async def download_video(message: types.Message):
    url = message.text.strip()
    if not url.startswith("http"):
        await message.answer("Iltimos, to'g'ri video havolasini yuboring!")
        return

    processing_msg = await message.answer("⏳ Video yuklab olinmoqda, biroz kuting...")

    output_file = "video.mp4"
    if os.path.exists(output_file):
        os.remove(output_file)

    ydl_opts = {
        'format': 'mp4',
        'outtmpl': output_file,
        'max_filesize': 50 * 1024 * 1024,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        if os.path.exists(output_file):
            await message.answer_video(types.FSInputFile(output_file))
            await processing_msg.delete()
            os.remove(output_file)
        else:
            await processing_msg.edit_text("Videoni yuklab bo'lmadi.")
    except Exception as e:
        await processing_msg.edit_text(f"Xatolik yuz berdi: {e}")

async def main():
    bot = Bot(token=TOKEN)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())