import os
import asyncio
import sqlite3
import logging
import aiohttp
from datetime import datetime
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, BotCommand, FSInputFile

# 1. Professional Logging sozlamasi
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Tokenni Render'dan o'qish
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("XATOLIK: Render'da BOT_TOKEN topilmadi!")

ADMIN_USERNAME = "@buxgalter_0011"
CHANNEL_USERNAME = "@open_budjet_20277"
ADMIN_USER_ID = None 

REFERRAL_BONUS = 500       # Har bir taklif qilingan do'st uchun beriladigan summa (so'm)
MIN_WITHDRAW_LIMIT = 15000  

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Anti-Flood uchun lug'atlar (5 tadan ko'p xabar yozsa 15 sekund kutish)
user_message_history = {}
user_cooldowns = {}

class VoteState(StatesGroup):
    waiting_for_phone = State()

# --- BAZA BILAN ISHLASH ---
def init_db():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            full_name TEXT,
            phone TEXT,
            balance INTEGER DEFAULT 0,
            invited_count INTEGER DEFAULT 0,
            votes_count INTEGER DEFAULT 0,
            referrer_id INTEGER DEFAULT 0,
            joined_date TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_user(user_id, full_name, referrer_id=0):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, referrer_id FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        ref = referrer_id if referrer_id != user_id else 0
        joined_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO users (user_id, full_name, phone, balance, invited_count, votes_count, referrer_id, joined_date) VALUES (?, ?, ?, 0, 1, 0, ?, ?)",
            (user_id, full_name, '', ref, joined_date)
        )
        if ref != 0:
            # Referal uchun bonus qo'shamiz
            cursor.execute("UPDATE users SET invited_count = invited_count + 1, balance = balance + ? WHERE user_id = ?", (REFERRAL_BONUS, ref))
        conn.commit()
    conn.close()

def update_user_phone(user_id, phone):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET phone = ? WHERE user_id = ?", (phone, user_id))
    conn.commit()
    conn.close()

def get_user_data(user_id):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT phone, balance, invited_count, votes_count, referrer_id FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"phone": row[0], "balance": row[1], "invited_count": row[2], "votes_count": row[3], "referrer_id": row[4]}
    return {"phone": "", "balance": 0, "invited_count": 0, "votes_count": 0, "referrer_id": 0}

def get_total_users_count():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_today_users_count():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("SELECT COUNT(*) FROM users WHERE joined_date LIKE ?", (f"{today}%",))
    count = cursor.fetchone()[0]
    conn.close()
    return count

async def check_subscription(user_id: int):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ["creator", "administrator", "member"]:
            return True
    except Exception as e:
        logging.error(f"Obunani tekshirishda xatolik: {e}")
        return False
    return False

# --- AVTOMATIK BACKUP TIZIMI ---
async def database_backup_task():
    await asyncio.sleep(30)
    while True:
        try:
            if ADMIN_USER_ID:
                if os.path.exists("bot_database.db"):
                    file = FSInputFile("bot_database.db")
                    await bot.send_document(
                        ADMIN_USER_ID, 
                        file, 
                        caption=f"📁 Avtomatik Database Backup: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                    )
        except Exception as e:
            logging.error(f"Backup yuborishda xatolik: {e}")
        await asyncio.sleep(86400)

# --- ANTI-FLOOD (5 tadan ko'p xabar yozsa 15 sekund bloklash) ---
@dp.message.middleware()
async def anti_flood_middleware(handler, event, data):
    if isinstance(event, types.Message) and event.from_user:
        user_id = event.from_user.id
        now = datetime.now().timestamp()
        
        if user_id in user_cooldowns and now < user_cooldowns[user_id]:
            left = int(user_cooldowns[user_id] - now)
            await event.answer(f"⚠️ Juda ko'p va tez yozdingiz! Iltimos, {left} sekund kuting.")
            return
        
        if user_id not in user_message_history:
            user_message_history[user_id] = []
        
        user_message_history[user_id] = [t for t in user_message_history[user_id] if now - t < 4.0]
        user_message_history[user_id].append(now)
        
        if len(user_message_history[user_id]) >= 5:
            user_cooldowns[user_id] = now + 15.0 
            user_message_history[user_id] = []
            await event.answer("⚠️ Juda tez-tez xabar yozganingiz uchun 15 sekundga bloklandingiz. Ozgina kuting!")
            return
            
    return await handler(event, data)

dp.message.middleware(anti_flood_middleware)

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🗳 Ovoz berish"), KeyboardButton(text="👥 Referal")],
        [KeyboardButton(text="💰 Hisobim"), KeyboardButton(text="📋 To'lovlar")],
        [KeyboardButton(text="👤 Admin bilan bog'lanish")],
    ],
    resize_keyboard=True,
)

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    full_name = message.from_user.first_name
    
    referrer_id = 0
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("ref"):
        referrer_str = args[1].replace("ref", "")
        if referrer_str.isdigit():
            referrer_id = int(referrer_str)

    # --- AUTO-VERIFY (Botga kirishi bilan obunani avtomatik tekshirish) ---
    is_subscribed = await check_subscription(user_id)
    if not is_subscribed:
        sub_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📢 Kanalga obuna bo'lish", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
                [InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="check_sub")]
            ]
        )
        add_user(user_id, full_name, referrer_id)
        await message.answer(
            f"Assalomu alaykum, **{full_name}**!\n\n"
            f"⚠️ Botdan to'liq foydalanish uchun avval rasmiy kanalimizga obuna bo'lishingiz kerak!",
            reply_markup=sub_keyboard,
            parse_mode="Markdown"
        )
        return

    add_user(user_id, full_name, referrer_id)

    welcome_text = (
        f"Assalomu alaykum, **{full_name}**!\n\n"
        f"🌟 **Open Budget** rasmiy ko'makchi botiga xush kelibsiz!\n"
        f"Quyidagi tugmalardan birini tanlang:"
    )
    await message.answer(text=welcome_text, reply_markup=main_keyboard, parse_mode="Markdown")

@dp.message(Command("help"))
async def cmd_help(message: types.Message, state: FSMContext):
    await state.clear()
    help_text = (
        "ℹ️ **Botdan foydalanish bo'yicha yo'riqnoma:**\n\n"
        "• **Ovoz berish** — Telefon raqamingizni qoldirib qatnashing.\n"
        "• **Referal** — Do'stlaringizni taklif qilib har biri uchun bonus oling.\n"
        "• **Hisobim** — Balansingizni ko'ring.\n"
        "• **To'lovlar** — Isbotlar kanalini kuzating.\n\n"
        f"Savollar bo'yicha: {ADMIN_USERNAME}"
    )
    await message.answer(help_text, parse_mode="Markdown")

@dp.callback_query(F.data == "check_sub")
async def callback_check_sub(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    is_subscribed = await check_subscription(user_id)
    
    if is_subscribed:
        await callback.message.delete()
        text = "Rahmat! Obuna tasdiqlandi. Marhamat, botdan foydalanishingiz mumkin:"
        await callback.message.answer(text=text, reply_markup=main_keyboard)
    else:
        await callback.answer("❌ Siz hali kanalga obuna bo'lmadingiz!", show_alert=True)

@dp.message(Command("admin"))
async def admin_panel(message: types.Message, state: FSMContext):
    global ADMIN_USER_ID
    await state.clear()
    if message.from_user.username != ADMIN_USERNAME.replace('@', ''):
        return
    
    ADMIN_USER_ID = message.from_user.id
    total_users = get_total_users_count()
    today_users = get_today_users_count()
    
    text = (
        f"👑 **Admin Boshqaruv Paneli**\n\n"
        f"📊 Jami foydalanuvchilar: {total_users} ta\n"
        f"📈 Bugun qo'shilganlar: {today_users} ta\n\n"
        f"📌 **Buyruqlar:**\n"
        f"• Hammaga xabar yuborish (rasm va tugma bilan): `/broadcast`"
    )
    await message.answer(text, parse_mode="Markdown")

# --- RASM VA TUGMALI BROADCAST (ADMIN UCHUN) ---
@dp.message(Command("broadcast"))
async def broadcast_handler(message: types.Message, state: FSMContext):
    if message.from_user.username != ADMIN_USERNAME.replace('@', ''):
        return
    
    text_to_send = message.text.replace("/broadcast", "").strip()
    if not text_to_send:
        await message.answer(
            "⚠️ **Broadcast ishlatish tartibi:**\n\n"
            "Matn yuborish uchun:\n`/broadcast Xabar matni`\n\n"
            "Rasm bilan yuborish uchun rasm tagiga izoh (caption) qilib yuboring.",
            parse_mode="Markdown"
        )
        return
    
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    conn.close()
    
    success, failed = 0, 0
    for u in users:
        try:
            if message.photo:
                photo_id = message.photo[-1].file_id
                await bot.send_photo(u[0], photo=photo_id, caption=message.caption or "")
            else:
                await bot.send_message(u[0], text_to_send)
            success += 1
            await asyncio.sleep(0.04)
        except Exception:
            failed += 1
            
    await message.answer(f"📢 Xabar tarqatildi!\n✅ Muvaffaqiyatli: {success}\n❌ Xato: {failed}")

@dp.message(F.text.func(lambda text: text and "Admin bilan bog'lanish" in text))
async def admin_contact_handler(message: types.Message, state: FSMContext):
    await state.clear()
    admin_inline = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💬 Adminga yozish", url=f"https://t.me/{ADMIN_USERNAME.replace('@', '')}")]
        ]
    )
    await message.answer(
        f"👤 Savollar bo'yicha adminimizga murojaat qiling: {ADMIN_USERNAME}",
        reply_markup=admin_inline
    )

@dp.message(F.text.func(lambda text: text and "Referal" in text))
async def referal_handler(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref{user_id}"
    
    text = (
        f"👥 **Sizning taklif havolangiz:**\n\n`{ref_link}`\n\n"
        f"📊 Taklif qilganlaringiz: {user_data['invited_count']} ta\n"
        f"🎁 Takliflar uchun berilgan bonus: {user_data['invited_count'] * REFERRAL_BONUS} so'm"
    )
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text.func(lambda text: text and "Hisobim" in text))
async def balance_handler(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    
    text = (
        f"👤 **Foydalanuvchi:** {message.from_user.first_name}\n"
        f"📱 **Telefon:** {user_data['phone'] if user_data['phone'] else 'Kiritilmagan'}\n"
        f"💰 **Balansingiz:** {user_data['balance']} so'm"
    )
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text.func(lambda text: text and "To'lovlar" in text))
async def proofs_handler(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("📋 Barcha isbotlar rasmiy kanalda e'lon qilinadi.", reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="📢 Kanal", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")] ]
    ))

@dp.message(F.text.func(lambda text: text and "Ovoz berish" in text))
async def vote_handler(message: types.Message, state: FSMContext):
    await state.clear()
    is_subscribed = await check_subscription(message.from_user.id)
    if not is_subscribed:
        await message.answer("⚠️ Avval kanalimizga obuna bo'ling!")
        return

    phone_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)],
            [KeyboardButton(text="🔙 Ortga")]
        ],
        resize_keyboard=True
    )
    await state.set_state(VoteState.waiting_for_phone)
    await message.answer("📱 Iltimos, telefon raqamingizni yuboring (Masalan: +998901234567):", reply_markup=phone_keyboard)

@dp.message(F.text == "🔙 Ortga")
async def back_handler(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Asosiy menyu:", reply_markup=main_keyboard)

@dp.message(VoteState.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext):
    phone = ""
    if message.contact:
        phone = message.contact.phone_number
    elif message.text:
        phone = message.text.strip()
        cleaned_phone = phone.replace("+", "").replace(" ", "").replace("-", "")
        if not cleaned_phone.isdigit() or len(cleaned_phone) < 9:
            await message.answer("❌ Noto'g'ri raqam kiritildi! Iltimos, to'g'ri formatda kiriting (Masalan: +998901234567):")
            return

    update_user_phone(message.from_user.id, phone)
    await message.answer("✅ Telefon raqamingiz muvaffaqiyatli saqlandi!", reply_markup=main_keyboard)
    await state.clear()

# --- SERVER VA SELF-PING ---
async def handle_ping(request):
    return web.Response(text="Bot is running safely!")

async def self_ping():
    url = "https://telagram-bot-0ftz.onrender.com"
    await asyncio.sleep(15)
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                async with session.get(url) as response:
                    logging.info(f"Self-ping status: {response.status}")
            except Exception as e:
                logging.error(f"Self-ping xatoligi: {e}")
            await asyncio.sleep(180)

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

async def main():
    init_db()
    await start_web_server()
    asyncio.create_task(self_ping())
    asyncio.create_task(database_backup_task())
    
    commands = [
        BotCommand(command="start", description="Botni qayta ishga tushirish"),
        BotCommand(command="help", description="Yordam va qo'llanma"),
        BotCommand(command="admin", description="Admin paneli (faqat admin uchun)")
    ]
    await bot.set_my_commands(commands)
    
    logging.info("Bot professional va xavfsiz rejimda ishga tushdi...")
    await bot.delete_webhook(drop_pending_updates=True)
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logging.critical(f"Kutilmagan xatolik tufayli bot to'xtadi: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot qo'lda to'xtatildi.")