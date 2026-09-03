import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiohttp import web

API_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

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
    text = (
        "Assalomu alaykum! Open Budget rasmiy ovoz berish botiga xush kelibsiz.\n\n"
        "Iltimos, kerakli bo‘limni tanlang:"
    )
    await message.answer(text=text, reply_markup=main_keyboard)

# 1. Ovoz berish bo'limi
@dp.message(lambda message: message.text == "🗳 Ovoz berish")
async def vote_handler(message: types.Message):
    text = (
        "🗳 **Ovoz berish tartibi:**\n\n"
        "1. Taqdim etilgan havola orqali o'ting.\n"
        "2. Ovoz bergandan so'ng, skrinshotni shu botga yuboring.\n\n"
        "Hozirda faol tanlovlar mavjud. Marhamat, ovozingizni qo'shing!"
    )
    await message.answer(text, parse_mode="Markdown")

# 2. Referal bo'limi (Foydalanuvchining o'z ID raqami bilan chiqadi)
@dp.message(lambda message: message.text == "👥 Referal")
async def referal_handler(message: types.Message):
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref{message.from_user.id}"
    text = (
        f"👥 **Sizning taklif havolangiz:**\n\n"
        f"`{ref_link}`\n\n"
        f"Do'stlaringizni taklif qiling va har bir ovoz uchun mukofot oling!"
    )
    await message.answer(text, parse_mode="Markdown")

# 3. Hisobim bo'limi
@dp.message(lambda message: message.text == "💰 Hisobim")
async def balance_handler(message: types.Message):
    text = (
        f"👤 **Foydalanuvchi:** {message.from_user.full_name}\n"
        f"🆔 **ID:** {message.from_user.id}\n"
        f"💰 **Balansingiz:** 0 so'm\n"
        f"🗳 **Tasdiqlangan ovozlaringiz:** 0 ta"
    )
    await message.answer(text, parse_mode="Markdown")

# 4. To'lov va isbotlar bo'limi
@dp.message(lambda message: message.text == "📋 To'lov va isbotlar")
async def proofs_handler(message: types.Message):
    text = (
        "📋 **Oxirgi amalga oshirilgan to'lovlar:**\n\n"
        "• ID ***4521 - 15,000 so'm ✅ (To'landi)\n"
        "• ID ***8910 - 20,000 so'm ✅ (To'landi)\n"
        "• ID ***1234 - 15,000 so'm ✅ (To'landi)\n\n"
        "Barcha to'lovlar o'z vaqtida amalga oshirilmoqda!"
    )
    await message.answer(text, parse_mode="Markdown")

# 5. Yordam / FAQ bo'limi
@dp.message(lambda message: message.text == "❓ Yordam / FAQ")
async def help_handler(message: types.Message):
    text = (
        "❓ **Ko'p beriladigan savollar:**\n\n"
        "1. Pulni qanday yechib olaman? — Balansingiz minimal miurdorga yetgach, adminga murojaat qilasiz.\n"
        "2. Ovoz qanday tekshiriladi? — Skrinshot yuborganingizdan so'ng 10 daqiqada tekshiriladi.\n\n"
        "Murojaat uchun: @Admin_Username"
    )
    await message.answer(text, parse_mode="Markdown")

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