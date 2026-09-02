import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
import yt_dlp

TOKEN = "8297785685:AAHjhwZVXjlenWqy7qQcpxeyawV2jsDLQEn5U"

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def command_start_handler(message: types.Message):
    await message.answer(
        "Salom! Menga YouTube, Instagram, TikTok, Facebook yoki Likee tarmoqlaridan video yoki audio havolasini yuboring, uni yuklab beraman."
    )

@dp.message()
async def download_media(message: types.Message):
    url = message.text.strip()
    if not url.startswith("http"):
        await message.answer("Iltimos, to'g'ri video yoki audio havolasini yuboring!")
        return

    # Check if the user wants audio or video.
    # For this example, we'll download video by default and audio if the user specifically mentions 'audio'.
    # You can customize this logic based on your needs.
    is_audio = "audio" in message.caption.lower() if message.caption else False

    processing_msg = await message.answer(
        "⏳ Media yuklab olinmoqda, biroz kuting..."
    )

    output_extension = "mp3" if is_audio else "mp4"
    output_file = f"media.{output_extension}"

    if os.path.exists(output_file):
        os.remove(output_file)

    ydl_opts = {
        'format': 'bestaudio/best' if is_audio else 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': output_file,
        'max_filesize': 50 * 1024 * 1024,
    }

    if is_audio:
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        if os.path.exists(output_file):
            if is_audio:
                await message.answer_audio(types.FSInputFile(output_file))
            else:
                await message.answer_video(types.FSInputFile(output_file))
            await processing_msg.delete()
            os.remove(output_file)
        else:
            await processing_msg.edit_text("Mediayo'lab bo'lmadi.")
    except Exception as e:
        await processing_msg.edit_text(f"Xatolik yuz berdi: {e}")

async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())