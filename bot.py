import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
import yt_dlp

# Tokenni environment variable'dan o'qiymiz (Render -> Environment -> BOT_TOKEN)
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError(
        "BOT_TOKEN topilmadi! Render dashboard -> Environment bo'limiga "
        "BOT_TOKEN nomi bilan tokeningizni qo'shing."
    )

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def command_start_handler(message: types.Message):
    await message.answer(
        "Salom! Menga YouTube, Instagram, TikTok, Facebook yoki Likee "
        "havolasini yuboring (yoki artist/qo'shiq nomini yozing), uni yuklab beraman."
    )


@dp.message()
async def download_media(message: types.Message):
    query = message.text.strip() if message.text else ""
    if not query:
        return

    if not query.startswith("http"):
        search_query = f"ytsearch1:{query}"
    else:
        search_query = query

    is_audio = "audio" in message.caption.lower() if message.caption else False

    processing_msg = await message.answer("Qidirilmoqda va yuklab olinmoqda, biroz kuting...")
    output_extension = "mp3" if is_audio else "mp4"
    output_file = f"media.{output_extension}"

    if os.path.exists(output_file):
        os.remove(output_file)

    ydl_opts = {
        'format': 'bestaudio/best' if is_audio else 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': output_file,
        'default_search': 'ytsearch',
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web'],
            }
        },
        'no_check_certificates': True,
    }

    if is_audio:
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([search_query])

        if os.path.exists(output_file):
            if is_audio:
                await message.answer_audio(types.FSInputFile(output_file))
            else:
                await message.answer_video(types.FSInputFile(output_file))
            await processing_msg.delete()
            os.remove(output_file)
        else:
            await processing_msg.edit_text("Hech narsa topilmadi yoki yuklab bo'lmadi.")
    except Exception as e:
        await processing_msg.edit_text(f"Xatolik yuz berdi: {e}")


async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
