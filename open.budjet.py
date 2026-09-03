import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiohttp import web

API_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Open Budget uchun maxsus ishlaydigan rasm havolasi
WELCOME_IMAGE_URL = "https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?q=80&w=1000&auto=format&fit=crop"

# Asosiy tugmalar menyusi
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🗳 Ovoz berish"), KeyboardButton(text="👥 Referal")],
        [KeyboardButton(text="💰 Hisobim"), KeyboardButton(text="📋 To'lov va isbotlar")],
        [KeyboardButton(text="❓ Yordam / FAQ")]
    ],
    resize_keyboard=True
)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    caption = (
        "Assalomu alaykum! Open Budget rasmiy ovoz berish botiga xush kelibsiz.\n\n"
        "Iltimos, kerakli bo‘limni tanlang:"
    )
    try:
        # Rasmli xabar yuborish
        await message.answer_photo(
            photo=WELCOME_IMAGE_URL,
            caption=caption,
            reply_markup=main_keyboard
        )
    except Exception as e:
        # Agar rasm yuklanishida xatol surat yuzaga kelsa, oddiy matn ko'rinishida yuboradi
        await message.answer(text=caption, reply_markup=main_keyboard)

# Tugmalar bosilganda ishlaydigan qism
@dp.message(lambda message: message.text == "🗳 Ovoz berish")
async def vote_handler(message: types.Message):
    await message.answer("Ovoz berish bo'limi hozircha tayyorlanmoqda 🛠")

@dp.message(lambda message: message.text == "👥 Referal")
async def referal_handler(message: types.Message):
    await message.answer("Sizning referal havolangiz:\nhttps://t.me/your_bot?start=ref123")

@dp.message(lambda message: message.text == "💰 Hisobim")
async def balance_handler(message: types.Message):
    await message.answer("Sizning balansingiz: 0 so'm")

@dp.message(lambda message: message.text == "📋 To'lov va isbotlar")
async def proofs_handler(message: types.Message):
    await message.answer("Hozircha to'lovlar mavjud emas.")

@dp.message(lambda message: message.text == "❓ Yordam / FAQ")
async def help_handler(message: types.Message):
    await message.answer("Savollar bo'yicha adminga murojaat qiling.")

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