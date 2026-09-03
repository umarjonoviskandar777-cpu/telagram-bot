import asyncio
import os
import sqlite3
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiohttp import web

API_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- SQLITE BAZASINI SOZLASH ---
def init_db():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            full_name TEXT,
            balance INTEGER DEFAULT 0,
            invited_count INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

# Foydalanuvchini bazaga qo'shish yoki tekshirish
def add_user(user_id, full_name):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        cursor.execute("INSERT INTO users (user_id, full_name, balance, invited_count) VALUES (?, ?, 0, 0)", (user_id, full_name))
        conn.commit()
    conn.close()

# Referalni qo'shish va taklif qilgan odamning sonini oshirish
def add_referral(referrer_id, new_user_id):
    if referrer_id == new_user_id:
        return
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    # Yangi foydalanuvchi oldin ro'yxatdan o'tganmi tekshiramiz
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (new_user_id,))
    user = cursor.fetchone()
    if not user:
        # Taklif qiluvchi bazada bormi tekshiramiz
        cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (referrer_id,))
        if cursor.fetchone():
            # Yangi foydalanuvchini qo'shamiz (taklif qilindi deb)
            cursor.execute("INSERT INTO users (user_id, full_name, balance, invited_count) VALUES (?, 'New User', 0, 0)", (new_user_id,))
            # Taklif qiluvchining invited_count miqdorini 1 taga oshiramiz
            cursor.execute("UPDATE users SET invited_count = invited_count + 1 WHERE user_id = ?", (referrer_id,))
            conn.commit()
    conn.close()

# Foydalanuvchi ma'lumotlarini olish
def get_user_data(user_id):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT balance, invited_count FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"balance": row[0], "invited_count": row[1]}
    return {"balance": 0, "invited_count": 0}

# Asosiy tugmalar menyusi
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🗳 Ovoz berish"), KeyboardButton(text="👥 Referal")],
        [KeyboardButton(text="💰 Hisobim"), KeyboardButton(text="📋 To'lov va isbotlar")],
        [KeyboardButton(text="❓ Yordam / FAQ")],
    ],
    resize_keyboard=True,
)


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    full_name = message.from_user.full_name
    
    # Foydalanuvchini bazaga kiritamiz
    add_user(user_id, full_name)

    # Referal orqali kirgan bo'lsa
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("ref"):
        referrer_str = args[1].replace("ref", "")
        if referrer_str.isdigit():
            add_referral(int(referrer_str), user_id)

    text = (
        "Assalomu alaykum! Open Budget rasmiy ovoz berish botiga xush kelibsiz.\n\n"
        "Iltimos, kerakli bo‘limni tanlang:"
    )
    await message.answer(text=text, reply_markup=main_keyboard)


# 1. Ovoz berish bo'limi
@dp.message(F.text == "🗳 Ovoz berish")
async def vote_handler(message: types.Message):
    channel_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📢 Kanalga o'tish", url="https://t.me/open_budjet_20277"
                )
            ]
        ]
    )
    text = (
        "🗳 **Ovoz berish tartibi:**\n\n"
        "1. Quyidagi tugma orqali rasmiy kanalimizga o'ting.\n"
        "2. Kanalda berilgan ko'rsatma bo'yicha ovoz bering.\n"
        "3. Ovoz berib bo'lgach, skrinshotni shu botga yuboring.\n\n"
        "Marhamat, kanalimizga o'ting!"
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=channel_keyboard)


# 2. Referal bo'limi
@dp.message(F.text == "👥 Referal")
async def referal_handler(message: types.Message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    invited_count = user_data["invited_count"]

    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref{user_id}"
    text = (
        f"👥 **Sizning taklif havolangiz:**\n\n"
        f"`{ref_link}`\n\n"
        f"📊 **Siz taklif qilgan do'stlaringiz soni:** {invited_count} ta\n\n"
        f"Do'stlaringizni taklif qiling va har bir ovoz uchun mukofot oling!"
    )
    await message.answer(text, parse_mode="Markdown")


# 3. Hisobim bo'limi
@dp.message(F.text == "💰 Hisobim")
async def balance_handler(message: types.Message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    
    text = (
        f"👤 **Foydalanuvchi:** {message.from_user.full_name}\n"
        f"🆔 **ID:** {user_id}\n"
        f"👥 **Taklif qilganlaringiz:** {user_data['invited_count']} ta\n"
        f"💰 **Balansingiz:** {user_data['balance']} so'm\n"
        f"🗳 **Tasdiqlangan ovozlaringiz:** 0 ta"
    )
    await message.answer(text, parse_mode="Markdown")


# 4. To'lov va isbotlar bo'limi
@dp.message(F.text == "📋 To'lov va isbotlar")
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
@dp.message(F.text == "❓ Yordam / FAQ")
async def help_handler(message: types.Message):
    channel_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📢 Bizning kanal", url="https://t.me/open_budjet_20277"
                )
            ]
        ]
    )
    text = (
        "❓ **Ko'p beriladigan savollar va yordam:**\n\n"
        "1. Pulni qanday yechib olaman? — Balansingiz minimal miqdorga yetgach, adminga murojaat qilasiz.\n"
        "2. Ovoz qanday tekshiriladi? — Skrinshot yuborganingizdan so'ng tekshiriladi.\n\n"
        "Barcha yangiliklar va ma'lumotlar quyidagi kanalimizda e'lon qilib boriladi:"
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=channel_keyboard)


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


if __name__ == "__main__":
    if not API_TOKEN:
        print("XATOLIK: BOT_TOKEN topilmadi.")
    else:
        # Bazani ishga tushirish
        init_db()
        try:
            async def run_all():
                await start_web_server()
                print("Bot ishga tushmoqda va baza ulandi...")
                await bot.delete_webhook(drop_pending_updates=True)
                await dp.start_polling(bot)

            asyncio.run(run_all())
        except KeyboardInterrupt:
            print("Bot to'xtatildi.")