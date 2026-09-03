import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiohttp import web

API_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Assalomu alaykum! Open Budget botiga xush kelibsiz.\n\nIltimos, kerakli bo‘limni tanlang:")

# Render port talabini qondirish uchun veb-server
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

if __name__ == '__main__':
    if not API_TOKEN:
        print("XATOLIK: BOT_TOKEN topilmadi.")
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