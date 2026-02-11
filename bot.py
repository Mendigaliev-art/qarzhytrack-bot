import asyncio
import calendar
import re
import os
import json
import gspread
from google.oauth2.service_account import Credentials


def gs_client():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    # ENV-тен Service Account JSON аламыз
    service_json = os.getenv("SERVICE_ACCOUNT_JSON")

    if not service_json:
        raise Exception("SERVICE_ACCOUNT_JSON жоқ! Render Environment Variables ішіне сал!")

    creds_dict = json.loads(service_json)

    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)

    return gspread.authorize(creds)

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder


# ✅ Render Environment Variables арқылы аламыз
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
SHEET_NAME = os.getenv("SHEET_NAME", "Обзор")

CATEGORIES = [
    "Бензин",
    "Развлечения",
    "Рестораны-кафе",
    "Ремонт, запчасть",
    "Благотворительность",
    "Бытовые расходы",
    "Кредит/Штраф/",
    "Семья",
    "Налоги",
    "Прочие расходы",
]

DATA_START_ROW = 3
COL_DATE = 2
COL_CATEGORY = 3
COL_AMOUNT = 4
COL_COMMENT = 5

PER_PAGE = 15

dp = Dispatcher()


# ---------------- Google Sheets ----------------
def gs_client():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    creds_dict = json.loads(SERVICE_ACCOUNT_JSON)

    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)


def ws():
    sh = gs_client().open_by_key(SPREADSHEET_ID)
    return sh.worksheet(SHEET_NAME)


def first_empty_row_in_col_b():
    w = ws()
    col_b = w.col_values(COL_DATE)
    last_filled = len(col_b)
    if last_filled < DATA_START_ROW - 1:
        return DATA_START_ROW
    return last_filled + 1


def write_expense(d, cat, amount, comment):
    w = ws()
    row = first_empty_row_in_col_b()
    w.update(f"B{row}:E{row}", [[d, cat, amount, comment]], value_input_option="RAW")


# ---------------- UI keyboards ----------------
def kb_main():
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Расход қосу", callback_data="m:add")
    kb.button(text="📊 Айлық есеп", callback_data="m:month")
    kb.adjust(1)
    return kb.as_markup()


# ---------------- Handlers ----------------
@dp.message(CommandStart())
async def start(m: Message):
    await m.answer("QarzhyTrack 💸 мәзір", reply_markup=kb_main())


@dp.callback_query(F.data == "m:add")
async def add_start(c: CallbackQuery):
    await c.message.answer("Соманы жаз: мысалы 5000 такси")
    await c.answer()


@dp.message()
async def on_text(m: Message):
    text = m.text.strip()

    match = re.search(r"\d+", text)
    if not match:
        await m.answer("Сома сан болуы керек")
        return

    amount = int(match.group())
    comment = text.replace(match.group(), "").strip()

    dstr = datetime.now().strftime("%d.%m.%Y")

    write_expense(dstr, "Прочие расходы", amount, comment)

    await m.answer("✅ Сақталды!", reply_markup=kb_main())


async def main():
    bot = Bot(TELEGRAM_TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
