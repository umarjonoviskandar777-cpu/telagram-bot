import asyncio
import logging
import sys
import sqlite3
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton

TOKEN = "8733052585:AAGX1pGDJl-LmQtvDQ_SZDGBLQ0FP45wfj8"

dp = Dispatcher()

# --- BAZA BILAN ISHLASH ---
def init_db():
    conn = sqlite3.connect("open_budget.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            referrer_id INTEGER,
            balance INTEGER DEFAULT 0,
            votes_count INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def add_user(user_id: int, referrer_id: int = None):
    conn = sqlite3.connect("open_budget.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        if referrer_id and referrer_id != user_id:
            cursor.execute("INSERT INTO users (user_id, referrer_id) VALUES (?, ?)", (user_id, referrer_id))
        else:
            cursor.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
    conn.close()

def get_user_stats(user_id: int):
    conn = sqlite3.connect("open_budget.db")
    cursor = conn.cursor()
    cursor.execute("SELECT balance, votes_count FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    
    # Taklif qilingan do'stlar sonini sanash
    cursor.execute("SELECT COUNT(*) FROM users WHERE referrer_id = ?", (user_id,))
    ref_count = cursor.fetchone()[0]
    
    conn.close()
    if result:
        return result[0], result[1], ref_count
    return 0, 0, ref_count

# --- MENYULAR ---
def reply_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🗳 Ovoz berish")],
            [KeyboardButton(text="👥 Referal"), KeyboardButton(text="💰 Hisobim")],
            [KeyboardButton(text="🧾 To'lov va isbotlar")],
            [KeyboardButton(text="❓ Yordam / FAQ")]
        ],
        resize_keyboard=True
    )
    return keyboard

def main_menu():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🗳 Ovoz berish", callback_data="vote")],
            [
                InlineKeyboardButton(text="👥 Referal", callback_data="referral"),
                InlineKeyboardButton(text="💰 Hisobim", callback_data="balance")
            ],
            [InlineKeyboardButton(text="🧾 To'lov va isbotlar", callback_data="proofs")],
            [
                InlineKeyboardButton(text="📢 Kanalga o'tish", url="https://t.me/open_budjet_20277"),
                InlineKeyboardButton(text="❓ Yordam / FAQ", callback_data="help")
            ]
        ]
    )
    return keyboard

# --- HANDLERLAR ---
@dp.message(CommandStart())
async def start_handler(message: Message, command: CommandObject):
    user_id = message.from_user.id
    args = command.args # Referal ID ni ushlab olish uchun
    
    referrer_id = None
    if args and args.isdigit():
        referrer_id = int(args)
    
    add_user(user_id, referrer_id)
    
    user_name = message.from_user.full_name
    text = (
        f"💥 <b>OXIRIDA OVOZ BERAMAN DEGAN AKALAR (OPALAR) 2 kun qoldi !!!</b>\n\n"
        f"🇺🇿 <b>Open Budjetga ishonchli ovozlarni olyabmiz, hoziroq ovoz bering!</b>\n\n"
        f"Assalomu alaykum, {user_name}! Kerakli bo'limni tanlang:"
    )
    await message.answer(text, reply_markup=reply_menu(), parse_mode="HTML")
    await message.answer("Asosiy menyu:", reply_markup=main_menu())

@dp.message(F.text == "🗳 Ovoz berish")
async def vote_text(message: Message):
    await message.answer(
        "🗳 <b>Ovoz berish uchun telefon raqamingizni kiriting:</b>\n\n"
        "Namuna: 91 123-45-67 yoki +998901234567",
        parse_mode="HTML"
    )

@dp.message(F.text == "👥 Referal")
async def referral_text(message: Message):
    user_id = message.from_user.id
    balance, votes, ref_count = get_user_stats(user_id)
    ref_link = f"https://t.me/open_budget_master_boT?start={user_id}"
    
    text = (
        "💥 <b>OXIRIDA OVOZ BERAMAN DEGAN AKALAR (OPALAR) 2 kun qoldi !!!</b>\n\n"
        "🇺🇿 <b>Open Budjetga ishonchli ovozlarni olyabmiz, hoziroq ovoz bering!</b>\n\n"
        "💵 <b>1ta ovoz - 26 ming soʻm</b>\n"
        "💵 <b>2ta ovoz - 55 ming soʻm</b>\n\n"
        "📊 <b>Sizning statistikangiz:</b>\n"
        f"👥 Jami taklif qilingan do'stlar: {ref_count} ta\n"
        f"🗳 Ovoz berganlar: {votes} ta\n"
        f"💵 Balans: {balance} so'm\n\n"
        f"⚡ <b>Toʻlovlar 100% boʻlmoqda, ishonchli cheklar:</b> @open_budjet_20277\n\n"
        f"🔗 <b>Sizning taklif havolangiz:</b>\n{ref_link}"
    )
    await message.answer(text, parse_mode="HTML")

@dp.message(F.text == "💰 Hisobim")
async def balance_text(message: Message):
    user_id = message.from_user.id
    balance, votes, ref_count = get_user_stats(user_id)
    text = (
        "👤 <b>Hisobingizdagi ma'lumotlar:</b>\n\n"
        "🆔 ID: <code>{}</code>\n"
        "💵 Joriy balans: {} so'm\n"
        "👥 Faol referallar: {} ta\n"
        "🗳 Tasdiqlangan ovozlar: {} ta\n\n"
        "👇 <b>Pul yechish uchun quyidagi tugmani bosing:</b>".format(user_id, balance, ref_count, votes)
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Pulni yechib olish", callback_data="withdraw")],
            [InlineKeyboardButton(text="📜 To'lovlar tarixi", callback_data="history")]
        ]
    )
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

@dp.message(F.text == "🧾 To'lov va isbotlar")
async def proofs_text(message: Message):
    await message.answer(
        "🧾 <b>To'lovlar isboti:</b>\n\n"
        "Foydalanuvchilarga barcha to'lovlar kanalimizda joylanadi.\n"
        "Kanalga o'tish uchun pastdagi tugmani bosing.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="📢 Kanalga o'tish", url="https://t.me/open_budjet_20277")]]
        ),
        parse_mode="HTML"
    )

@dp.message(F.text == "❓ Yordam / FAQ")
async def help_text(message: Message):
    text = (
        "❓ <b>Yordam / FAQ:</b>\n\n"
        "1. <b>Referal qanday ishlaydi?</b>\n"
        "O'zingizning havolangiz orqali do'stingizni taklif qiling, OpenBudgetda ovoz bersa – sizga pul beriladi.\n\n"
        "2. <b>Pulni qachon yechish mumkin?</b>\n"
        "Minimal yechish summasiga yetgach 💼 Hisobim bo'limi orqali so'rov yuborasiz."
    )
    await message.answer(text, parse_mode="HTML")

# Inline tugmalar handlerlari
@dp.callback_query(F.data == "vote")
async def vote_callback(callback: CallbackQuery):
    await callback.message.answer(
        "🗳 <b>Ovoz berish uchun telefon raqamingizni kiriting:</b>\n\n"
        "Namuna: 91 123-45-67 yoki +998901234567",
        parse_mode="HTML"
    )
    await callback.answer()

@dp.callback_query(F.data == "referral")
async def referral_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    balance, votes, ref_count = get_user_stats(user_id)
    ref_link = f"https://t.me/open_budget_master_boT?start={user_id}"
    text = (
        "💵 <b>1ta ovoz - 26 ming soʻm</b>\n"
        "💵 <b>2ta ovoz - 55 ming soʻm</b>\n\n"
        f"👥 Taklif qilinganlar: {ref_count} ta\n"
        f"💵 Balans: {balance} so'm\n\n"
        f"🔗 <b>Sizning havolangiz:</b>\n{ref_link}"
    )
    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "balance")
async def balance_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    balance, votes, ref_count = get_user_stats(user_id)
    text = (
        "👤 <b>Hisob ma'lumotlaringiz:</b>\n\n"
        "🆔 ID: <code>{}</code>\n"
        "💵 Balans: {} so'm\n"
        "👥 Referallar: {} ta".format(user_id, balance, ref_count)
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Pulni yechib olish", callback_data="withdraw")],
            [InlineKeyboardButton(text="📜 To'lovlar tarixi", callback_data="history")]
        ]
    )
    await callback.message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "proofs")
async def proofs_callback(callback: CallbackQuery):
    await callback.message.answer(
        "🧾 <b>To'lovlar isboti:</b> @open_budjet_20277 kanalida!",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="📢 Kanalga o'tish", url="https://t.me/open_budjet_20277")]]
        ),
        parse_mode="HTML"
    )
    await callback.answer()

@dp.callback_query(F.data == "help")
async def help_callback(callback: CallbackQuery):
    await callback.message.answer("❓ Savollar bo'yicha administratorga murojaat qiling.", parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "withdraw")
async def withdraw_callback(callback: CallbackQuery):
    await callback.message.answer("⚠️ Minimal yechish miqdoriga yetmagansiz!")
    await callback.answer()

@dp.callback_query(F.data == "history")
async def history_callback(callback: CallbackQuery):
    await callback.message.answer("📜 Sizda hali to'lovlar tarixi mavjud emas.")
    await callback.answer()

async def main():
    init_db()
    bot = Bot(token=TOKEN)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
    input("\nBot to'xtatildi. Chiqish uchun Enter tugmasini bosing...")