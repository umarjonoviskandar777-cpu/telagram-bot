import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Tokeningiz
TOKEN = "8733052585:AA..."  # O'zingizning bot tokeningiz

# Open Budget ovoz berish havolasi
OPEN_BUDGET_LINK = "https://openbudget.uz/boards/2/..." 

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

class VoteState(StatesGroup):
    waiting_for_phone = State()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🗳 Ovoz berish", callback_data="start_vote")],
            [InlineKeyboardButton(text="👤 Mening hisobim", callback_data="my_account")],
            [InlineKeyboardButton(text="📢 Kanalga o'tish", url="https://t.me/open_budjet_20277")]
        ]
    )
    await message.answer(
        f"Assalomu alaykum, {message.from_user.first_name}!\n"
        "Open Budgetga ishonchli ovozlarni olyapmiz, hozir ovoz bering!",
        reply_markup=keyboard
    )

@dp.callback_query(lambda c: c.data == "start_vote")
async def process_vote(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Iltimos, telefon raqamingizni yuboring (masalan: +998901234567):")
    await state.set_state(VoteState.waiting_for_phone)
    await callback.answer()

@dp.message(VoteState.waiting_for_phone)
async def receive_phone(message: types.Message, state: FSMContext):
    phone = message.text
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👉 Ovoz berish sahifasiga o'tish", url=OPEN_BUDGET_LINK)]
        ]
    )
    await message.answer(
        "Rahmat! Raqamingiz qabul qilindi.\n\n"
        "Endi quyidagi tugmani bosib, ovoz bering:",
        reply_markup=keyboard
    )
    await state.clear()

@dp.callback_query(lambda c: c.data == "my_account")
async def my_account(callback: types.CallbackQuery):
    await callback.message.answer("Sizning hisobingizda hali ovozlar yo'q.")
    await callback.answer()

if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))