import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.types import BufferedInputFile

# Tokenni Render’dagi environment variable’dan o‘qiymiz
API_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Xush kelibsiz rasmining URL manzili (agar o‘zingizniki bo‘lsa, o‘zgartiring)
WELCOME_IMAGE_URL = "https://telegra.ph/file/131d4a98c535864ea8c8e.jpg"

async def send_welcome_image(chat_id):
    """Bot ishga tushganda yoki yangi foydalanuvchiga rasmni yuboradi."""
    try:
        # Rasm URL orqali yuklanadi
        caption = "Assalomu alaykum! Open Budget botiga xush kelibsiz.\n\nIltimos, kerakli bo‘limni tanlang:"
        await bot.send_photo(chat_id=chat_id, photo=WELCOME_IMAGE_URL, caption=caption)
    except Exception as e:
        print(f"Xatolik yuz berdi: {e}")

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """ /start komandasi uchun handler """
    # Foydalanuvchiga rasm va matnni yuboramiz
    await send_welcome_image(message.chat.id)

    # Quyida o'zingizning tugmalaringizni qo'shishingiz mumkin
    # Masalan:
    # markup = types.ReplyKeyboardMarkup(...)
    # await message.answer("Asosiy menyu:", reply_markup=markup)

# Botni ishga tushirish
async def main():
    print("Bot ishga tushmoqda...")
    # Eskilarni tozalash (uzoq vaqt o'chib qolganda kerak bo'lishi mumkin)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    if not API_TOKEN:
        print("XATOLIK: BOT_TOKEN topilmadi. Render.com sozlamalarini tekshiring.")
    else:
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            print("Bot to'xtatildi.")