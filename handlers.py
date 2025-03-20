# handlers.py
from aiogram import Dispatcher, types
from config import MASTER_ADMIN_ID, MASTER_PASSWORD
from database import init_db, add_admin, get_admin, get_all_admins, log_action

MENU_TEXTS = {
    "fa": {
        "main_menu": ["لیست کانال‌ها", "اضافه کردن کانال", "تنظیمات", "ترجمه متن", "توقف ربات", "آمار"],
        "welcome": "خوش اومدی! لطفاً از منو انتخاب کن:",
        "master_init": "لطفاً کلمه رمز رو بفرست تا مستر ادمین ثبت بشی:",
        "master_success": "شما به عنوان مستر ادمین ثبت شدید!",
        "not_admin": "شما ادمین نیستید!"
    }
}

def get_main_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for item in MENU_TEXTS["fa"]["main_menu"]:
        keyboard.add(types.KeyboardButton(item))
    return keyboard

async def start_command(message: types.Message):
    admin = get_admin(message.from_user.id)
    if not admin and message.from_user.id == MASTER_ADMIN_ID and not get_all_admins():
        await message.reply(MENU_TEXTS["fa"]["master_init"])
        log_action(message.from_user.id, "Master init requested")
        return
    if not admin:
        await message.reply(MENU_TEXTS["fa"]["not_admin"])
        return
    await message.reply(MENU_TEXTS["fa"]["welcome"], reply_markup=get_main_keyboard())

async def handle_message(message: types.Message):
    text = message.text
    log_action(message.from_user.id, f"Received: {text}")  # لاگ برای دیباگ
    admin = get_admin(message.from_user.id)

    if not admin and message.from_user.id == MASTER_ADMIN_ID and text == MASTER_PASSWORD:
        try:
            add_admin(message.from_user.id, "master_admin")
            log_action(message.from_user.id, "Master admin registered")
            await message.reply(MENU_TEXTS["fa"]["master_success"], reply_markup=get_main_keyboard())
        except Exception as e:
            log_action(message.from_user.id, f"Error registering master: {str(e)}")
            await message.reply(f"خطا: {str(e)}")
        return

    if admin:
        await message.reply(f"پیامت دریافت شد: {text}", reply_markup=get_main_keyboard())
    else:
        await message.reply(MENU_TEXTS["fa"]["not_admin"])

def register_handlers(dp: Dispatcher):
    dp.register_message_handler(start_command, commands=["start"])
    dp.register_message_handler(handle_message, content_types=["text"])
