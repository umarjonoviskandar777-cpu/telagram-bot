import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiohttp import web

# Tokenni Render’dagi environment variable’dan o‘qiymiz
API_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Xush kelibsiz rasmining URL manzili
WELCOME_IMAGE_URL = "https://telegra.ph/file/131d4a98c535864ea8c8e.jpg"

async def send_welcome_image(chat_id):
    """Bot ishga tushganda yoki yangi foydalanuvchiga rasmni yuboradi."""
    try:
        caption = "Assalomu alaykum! Open Budget botiga xush kelibsiz.\n\nIltimos, kerakli bo‘limni tanlang:"
        await bot.send_photo(chat_id=chat_id, photo=WELCOME_IMAGE_URL, caption=caption)
    except Exception as e:
        print(f"Xatolik yuz berdi: {e}")

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """ /start komandasi uchun handler """
    await send_welcome_image(message.chat.id)

# Render port talabini qondirish uchun kichik veb-server
async def handle(request):
    return web.Response(text="Bot ishlayapti!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

# Hammasini bir vaqtda xatosiz ishga tushirish
if __name__ == '__main__':
    if not API_TOKEN:
        print("XATOLIK: BOT_TOKEN topilmadi. Render.com sozlamalarini tekshiring.")
    else:
        try:
            async def run_all():
                await start_web_server()
                print("Bot ishga tushmoqda...")
                await bot.delete_webhook(drop_pending_updates=True)
                await dp.start_polling(bot)

            asyncio.run(run_all())
        except KeyboardInterrupt:
            print("Bot to'xtatildi.")