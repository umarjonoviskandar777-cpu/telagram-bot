import os
import asyncio
import sqlite3
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

# Tokenni Render'dagi Environment Variables'dan avtomatik o'qiydi
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("XATOLIK: Render'da BOT_TOKEN topilmadi!")

ADMIN_USERNAME = "@buxgalter_0011"
CHANNEL_USERNAME = "@open_budjet_20277"

VOTE_REWARD = 0       
REFERRAL_BONUS = 0       
MIN_WITHDRAW_LIMIT = 15000  

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

class VoteState(StatesGroup):
    waiting_for_phone = State()
    waiting_for_screenshot = State()

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
            referrer_id INTEGER DEFAULT 0
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
        cursor.execute("INSERT INTO users (user_id, full_name, phone, balance, invited_count, votes_count, referrer_id) VALUES (?, ?, '', 0, 0, 0, ?)", (user_id, full_name, ref))
        if ref != 0:
            cursor.execute("UPDATE users SET invited_count = invited_count + 1 WHERE user_id = ?", (ref,))
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

async def check_subscription(user_id: int):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ["creator", "administrator", "member"]:
            return True
    except Exception as e:
        print(f"Obunani tekshirishda xatolik: {e}")
        return False
    return False

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
            f"Assalomu alaykum, **{full_name}** !\n\n"
            f"⚠️ Botdan to'liq foydalanish uchun avval rasmiy kanalimizga obuna bo'lishingiz kerak!",
            reply_markup=sub_keyboard,
            parse_mode="Markdown"
        )
        return

    add_user(user_id, full_name, referrer_id)

    welcome_text = (
        f"Assalomu alaykum, **{full_name}** !\n\n"
        f"🌟 **Open Budget** rasmiy ko'makchi botiga xush kelibsiz!\n"
        f"Hozirda mavsum oralig'idamiz. Mavsum boshlanganda ovoz berish va mukofotlar to'liq faollashadi.\n\n"
        f"Quyidagi tugmalardan birini tanlang:"
    )
    await message.answer(text=welcome_text, reply_markup=main_keyboard, parse_mode="Markdown")

@dp.callback_query(F.data == "check_sub")
async def callback_check_sub(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    is_subscribed = await check_subscription(user_id)
    
    if is_subscribed:
        await callback.message.delete()
        text = "Rahmat! Obuna tasdiqlandi. Marhamat, botdan foydalanishingiz mumkin:"
        await callback.message.answer(text=text, reply_markup=main_keyboard)
    else:
        await callback.answer("❌ Siz hali kanalga obuna bo'lmadingiz yoki bot kanalda admin emas!", show_alert=True)

@dp.message(Command("admin"))
async def admin_panel(message: types.Message, state: FSMContext):
    await state.clear()
    if message.from_user.username != ADMIN_USERNAME.replace('@', ''):
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
async def broadcast_handler(message: types.Message, state: FSMContext):
    await state.clear()
    if message.from_user.username != ADMIN_USERNAME.replace('@', ''):
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
        f"👤 Savollar va takliflar bo'yicha to'g'ridan-to'g'ri adminimizga murojaat qilishingiz mumkin: {ADMIN_USERNAME}",
        reply_markup=admin_inline
    )

@dp.message(F.text.func(lambda text: text and "Referal" in text))
async def referal_handler(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    user_data = get_user_data(user_id)

    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref{user_id}"
    
    share_url = f"https://t.me/share/url?url={ref_link}&text=🌟+Open+Budget+botiga+kiring+va+obuna+bo'ling!"
    
    ref_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="↗️ Do'stlarga ulashish", url=share_url)]
        ]
    )

    text = (
        f"👥 **Sizning taklif havolangiz:**\n\n"
        f"`{ref_link}`\n\n"
        f"📊 **Siz taklif qilgan do'stlaringiz soni:** {user_data['invited_count']} ta\n\n"
        f"Do'stlaringizni taklif qilib bazamizni kengaytiring!"
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=ref_keyboard)

@dp.message(F.text.func(lambda text: text and "Hisobim" in text))
async def balance_handler(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    
    withdraw_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💸 Pulni yechib olish", callback_data="withdraw_request")],
            [InlineKeyboardButton(text="👤 Admin bilan bog'lanish", url=f"https://t.me/{ADMIN_USERNAME.replace('@', '')}")]
        ]
    )
    
    text = (
        f"👤 **Foydalanuvchi:** {message.from_user.first_name}\n"
        f"🆔 **ID:** {user_id}\n"
        f"📱 **Telefon:** {user_data['phone'] if user_data['phone'] else 'Kiritilmagan'}\n"
        f"👥 **Taklif qilganlaringiz:** {user_data['invited_count']} ta\n"
        f"💰 **Balansingiz:** {user_data['balance']} so'm\n"
        f"🗳 **Tasdiqlangan ovozlaringiz:** {user_data['votes_count']} ta"
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=withdraw_keyboard)

@dp.callback_query(F.data == "withdraw_request")
async def withdraw_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_data = get_user_data(user_id)
    
    if user_data['balance'] < MIN_WITHDRAW_LIMIT:
        await callback.answer(f"❌ Pul yechib olish uchun minimal summa {MIN_WITHDRAW_LIMIT} so'm bo'lishi kerak!", show_alert=True)
        return
        
    await callback.message.answer(
        f"✅ Pulni yechish uchun arizangiz tayyorlandi!\n"
        f"Iltimos, ushbu summani olish uchun adminimizga yozing: {ADMIN_USERNAME}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💬 Adminga yozish", url=f"https://t.me/{ADMIN_USERNAME.replace('@', '')}")]
        ])
    )
    await callback.answer()

@dp.message(F.text.func(lambda text: text and "To'lovlar" in text))
async def proofs_handler(message: types.Message, state: FSMContext):
    await state.clear()
    channel_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📢 Isbotlar kanali", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")]
        ]
    )
    text = (
        "📋 **To'lovlar va isbotlar bo'limi:**\n\n"
        "Barcha amalga oshirilgan to'lovlar va muvaffaqiyatli ovozlar quyidagi rasmiy kanalimizda e'lon qilib boriladi:\n\n"
        "• Mavsum oralig'ida yangiliklar kanalda e'lon qilinadi ✅"
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=channel_keyboard)

@dp.message(F.text.func(lambda text: text and "Ovoz berish" in text))
async def vote_handler(message: types.Message, state: FSMContext):
    await state.clear()
    is_subscribed = await check_subscription(message.from_user.id)
    if not is_subscribed:
        await message.answer("⚠️ Avval kanalimizga obuna bo'ling! /start buyrug'ini bosing.")
        return

    phone_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)],
            [KeyboardButton(text="🔙 Ortga")]
        ],
        resize_keyboard=True
    )

    text = (
        "🗳 **Ovoz berish tartibi:**\n\n"
        "Hozirda Open Budget mavsumi tugagan. Lekin sinov tariqasida telefon raqamingizni qoldirishingiz mumkin:\n\n"
        "Namuna: `91 123-45-67` yoki +998901234567"
    )
    await state.set_state(VoteState.waiting_for_phone)
    await message.answer(text, parse_mode="Markdown", reply_markup=phone_keyboard)

@dp.message(F.text == "🔙 Ortga")
async def back_handler(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Asosiy menyuga qaydingiz:", reply_markup=main_keyboard)

@dp.message(VoteState.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext):
    phone = ""
    if message.contact:
        phone = message.contact.phone_number
    elif message.text:
        phone = message.text.strip()
    else:
        await message.answer("Iltimos, telefon raqamingizni to'g'ri kiriting yoki tugmani bosing.")
        return

    update_user_phone(message.from_user.id, phone)
    
    text = (
        "✅ Telefon raqamingiz saqlandi!\n\n"
        "🗳 Mavsum boshlanganda ushbu raqam orqali ovoz berish imkoniyati ochiladi."
    )
    await message.answer(text, reply_markup=main_keyboard)
    await state.clear()

# Render veb-servis uchun port ochib turuvchi qism
async def handle_ping(request):
    return web.Response(text="Bot is running!")

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
    print("Bot to'liq professional va barqaror holda ishga tushmoqda...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot to'xtatildi.")