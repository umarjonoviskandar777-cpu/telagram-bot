import asyncio
import os
import sqlite3
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiohttp import web

API_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 7417357436  
CHANNEL_USERNAME = "@open_budjet_20277"

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
            invited_count INTEGER DEFAULT 0,
            votes_count INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def add_user(user_id, full_name):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        cursor.execute("INSERT INTO users (user_id, full_name, balance, invited_count, votes_count) VALUES (?, ?, 0, 0, 0)", (user_id, full_name))
        conn.commit()
    conn.close()

def add_referral(referrer_id, new_user_id):
    if referrer_id == new_user_id:
        return
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (new_user_id,))
    user = cursor.fetchone()
    if not user:
        cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (referrer_id,))
        if cursor.fetchone():
            cursor.execute("INSERT INTO users (user_id, full_name, balance, invited_count, votes_count) VALUES (?, 'New User', 0, 0, 0)", (new_user_id,))
            cursor.execute("UPDATE users SET invited_count = invited_count + 1 WHERE user_id = ?", (referrer_id,))
            conn.commit()
    conn.close()

def get_user_data(user_id):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT balance, invited_count, votes_count FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"balance": row[0], "invited_count": row[1], "votes_count": row[2]}
    return {"balance": 0, "invited_count": 0, "votes_count": 0}

def get_total_users_count():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count

# Kanalga obuna bo'lganini tekshirish
async def check_subscription(user_id: int):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ["creator", "administrator", "member"]:
            return True
    except Exception as e:
        print(f"Obunani tekshirishda xatolik (Bot kanalda admin ekanligini tekshiring!): {e}")
        # Agar bot admin bo'lmasa yoki xato bo'lsa ham ishlayverishi uchun sinov tariqasida True qaytarish mumkin, 
        # lekin kanalga odam yig'ish uchun bot kanalga admin bo'lishi shart!
        return False
    return False

# Asosiy tugmalar menyusi (Matnlar qisqartirildi va aniq qilindi)
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🗳 Ovoz berish"), KeyboardButton(text="👥 Referal")],
        [KeyboardButton(text="💰 Hisobim"), KeyboardButton(text="📋 To'lovlar")],
        [KeyboardButton(text="❓ Yordam")],
    ],
    resize_keyboard=True,
)


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    full_name = message.from_user.full_name
    
    is_subscribed = await check_subscription(user_id)
    if not is_subscribed:
        sub_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📢 Kanalga obuna bo'lish", url="https://t.me/open_budjet_20277")],
                [InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="check_sub")]
            ]
        )
        await message.answer(
            "⚠️ Botdan foydalanish uchun avval rasmiy kanalimizga obuna bo'lishingiz kerak!",
            reply_markup=sub_keyboard
        )
        return

    add_user(user_id, full_name)

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


@dp.callback_query(F.data == "check_sub")
async def callback_check_sub(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    is_subscribed = await check_subscription(user_id)
    
    if is_subscribed:
        add_user(user_id, callback.from_user.full_name)
        await callback.message.delete()
        text = "Rahmat! Obuna tasdiqlandi. Marhamat, botdan foydalanishingiz mumkin:"
        await callback.message.answer(text=text, reply_markup=main_keyboard)
    else:
        await callback.answer("❌ Siz hali kanalga obuna bo'lmadingiz yoki bot kanalda admin emas!", show_alert=True)


# --- ADMIN PANEL & STATISTIKA & RASSILKA ---
@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    total_users = get_total_users_count()
    text = (
        f"👑 **Admin Boshqaruv Paneli**\n\n"
        f"📊 Botdagi jami foydalanuvchilar: {total_users} ta\n\n"
        f"📌 **Buyruqlar:**\n"
        f"• Hamma foydalanuvchilarga xabar yuborish uchun: `/broadcast [xabar matni]` yozing."
    )
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("broadcast"))
async def broadcast_handler(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    text_to_send = message.text.replace("/broadcast", "").strip()
    if not text_to_send:
        await message.answer("⚠️ Yuboriladigan xabar matnini kiriting. Masalan: `/broadcast Salom hammaga!`", parse_mode="Markdown")
        return
    
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    conn.close()
    
    success = 0
    failed = 0
    for u in users:
        try:
            await bot.send_message(u[0], text_to_send)
            success += 1
            await asyncio.sleep(0.04)
        except Exception:
            failed += 1
            
    await message.answer(f"📢 Xabar tarqatildi!\n✅ Muvaffaqiyatli: {success}\n❌ Xato (botni bloklaganlar): {failed}")


# 1. Ovoz berish bo'limi
@dp.message(F.text == "🗳 Ovoz berish")
async def vote_handler(message: types.Message):
    is_subscribed = await check_subscription(message.from_user.id)
    if not is_subscribed:
        await message.answer("⚠️ Avval kanalimizga obuna bo'ling! /start buyrug'ini bosing.")
        return

    text = (
        "🗳 **Ovoz berish tartibi:**\n\n"
        "1. Open Budget portalida bizning loyihamizga ovoz bering.\n"
        "2. Ovoz berganingizni tasdiqlovchi **skrinshotni** to'g'ridan-to'g'ri shu botga yuboring.\n\n"
        "Marhamat, skrinshotni yuboring!"
    )
    await message.answer(text, parse_mode="Markdown")


# Skrinshot qabul qilish va adminga yuborish
@dp.message(F.photo)
async def photo_handler(message: types.Message):
    user_id = message.from_user.id
    full_name = message.from_user.full_name
    
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET votes_count = votes_count + 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

    caption = (
        f"📥 **Yangi ovoz skrinshoti keldi!**\n\n"
        f"👤 Foydalanuvchi: {full_name}\n"
        f"🆔 ID: `{user_id}`"
    )
    await bot.send_photo(chat_id=ADMIN_ID, photo=message.photo[-1].file_id, caption=caption, parse_mode="Markdown")
    await message.answer("✅ Skrinshotiz adminga yuborildi! Tekshirilgach balansingizga qo'shiladi.")


# 2. Referal bo'limi
@dp.message(F.text == "👥 Referal")
async def referal_handler(message: types.Message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)

    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref{user_id}"
    text = (
        f"👥 **Sizning taklif havolangiz:**\n\n"
        f"`{ref_link}`\n\n"
        f"📊 **Siz taklif qilgan do'stlaringiz soni:** {user_data['invited_count']} ta\n\n"
        f"Do'stlaringizni taklif qiling va har bir ovoz uchun mukofot oling!"
    )
    await message.answer(text, parse_mode="Markdown")


# 3. Hisobim bo'limi
@dp.message(F.text == "💰 Hisobim")
async def balance_handler(message: types.Message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    
    withdraw_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💸 Pulni yechib olish", callback_data="withdraw_request")]
        ]
    )
    
    text = (
        f"👤 **Foydalanuvchi:** {message.from_user.full_name}\n"
        f"🆔 **ID:** {user_id}\n"
        f"👥 **Taklif qilganlaringiz:** {user_data['invited_count']} ta\n"
        f"💰 **Balansingiz:** {user_data['balance']} so'm\n"
        f"🗳 **Tasdiqlangan ovozlaringiz:** {user_data['votes_count']} ta"
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=withdraw_keyboard)

@dp.callback_query(F.data == "withdraw_request")
async def withdraw_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_data = get_user_data(user_id)
    
    if user_data['balance'] <= 0:
        await callback.answer("❌ Balansingizda mablag' yetarli emas!", show_alert=True)
        return
        
    admin_text = (
        f"💸 **Yangi pul yechish arizasi!**\n\n"
        f"👤 Foydalanuvchi: {callback.from_user.full_name}\n"
        f"🆔 ID: `{user_id}`\n"
        f"💰 Summa: {user_data['balance']} so'm"
    )
    await bot.send_message(chat_id=ADMIN_ID, text=admin_text, parse_mode="Markdown")
    await callback.message.answer("✅ Pulni yechish uchun arizangiz adminga yuborildi. Tez orada ko'rib chiqiladi!")
    await callback.answer()


# 4. To'lovlar bo'limi
@dp.message(F.text == "📋 To'lovlar")
async def proofs_handler(message: types.Message):
    channel_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📢 Isbotlar kanali", url="https://t.me/open_budjet_20277")]
        ]
    )
    text = (
        "📋 **To'lovlar va isbotlar bo'limi:**\n\n"
        "Barcha amalga oshirilgan to'lovlar va muvaffaqiyatli ovozlar quyidagi rasmiy kanalimizda e'lon qilib boriladi:\n\n"
        "• Oxirgi to'lovlar o'z vaqtida tarqatilmoqda ✅"
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=channel_keyboard)


# 5. Yordam bo'limi
@dp.message(F.text == "❓ Yordam")
async def help_handler(message: types.Message):
    text = (
        "❓ **Ko'p beriladigan savollar va yordam:**\n\n"
        "1. Pulni qanday yechib olaman? — 'Hisobim' bo'limidagi tugma orqali ariza qoldirasiz.\n"
        "2. Ovoz qanday tekshiriladi? — Skrinshot yuborganingizdan so'ng tekshiriladi.\n\n"
        "Savollar bo'yicha: @Admin_Username"
    )
    await message.answer(text, parse_mode="Markdown")


# Render server
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
        init_db()
        try:
            async def run_all():
                await start_web_server()
                print("Bot ishga tushmoqda, baza va admin panellar ulandi...")
                await bot.delete_webhook(drop_pending_updates=True)
                await dp.start_polling(bot)

            asyncio.run(run_all())
        except KeyboardInterrupt:
            print("Bot to'xtatildi.")