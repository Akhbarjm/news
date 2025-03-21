from aiogram import Dispatcher, types
from config import MASTER_ADMIN_ID, MASTER_PASSWORD

MENU_TEXTS = {
    "fa": {
        "main_menu": ["لیست کانال‌ها", "اضافه کردن کانال", "تنظیمات", "ترجمه متن", "توقف ربات", "آمار"],
        "welcome": "خوش اومدی! لطفاً از منو انتخاب کن:",
        "master_init": "لطفاً کلمه رمز رو بفرست تا مستر ادمین ثبت بشی:",
        "master_success": "شما به عنوان مستر ادمین ثبت شدید!",
        "not_admin": "شما ادمین نیستید!",
        "channels_list": "لیست کانال‌ها خالیه! یه کانال اضافه کن.",
        "add_channel": "لطفاً آیدی کانال رو بفرست (مثل @ChannelName):",
        "channel_added": "کانال با موفقیت اضافه شد!",
        "settings": "تنظیمات فعلاً خالیه!",
        "translate_prompt": "متن رو بفرست تا ترجمه کنم (به انگلیسی):",
        "stop_bot": "ربات متوقف شد! برای شروع دوباره /start بزن.",
        "stats": "آمار: هنوز چیزی نداریم!"
    }
}

channels = []  # لیست کانال‌ها رو اینجا نگه می‌داریم

def get_main_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for item in MENU_TEXTS["fa"]["main_menu"]:
        keyboard.add(types.KeyboardButton(item))
    return keyboard

async def start_command(message: types.Message):
    if message.from_user.id == MASTER_ADMIN_ID:
        await message.reply(MENU_TEXTS["fa"]["master_init"])
        print(f"Master init requested by {message.from_user.id}")
    else:
        await message.reply(MENU_TEXTS["fa"]["not_admin"])

async def handle_message(message: types.Message):
    text = message.text
    print(f"Received: {text} from {message.from_user.id}")

    # ثبت مستر ادمین
    if message.from_user.id == MASTER_ADMIN_ID and text == MASTER_PASSWORD:
        await message.reply(MENU_TEXTS["fa"]["master_success"], reply_markup=get_main_keyboard())
        print(f"Master admin registered: {message.from_user.id}")
        return

    # فقط مستر ادمین می‌تونه ادامه بده
    if message.from_user.id != MASTER_ADMIN_ID:
        await message.reply(MENU_TEXTS["fa"]["not_admin"])
        return

    # منوها
    if text == "لیست کانال‌ها":
        if not channels:
            await message.reply(MENU_TEXTS["fa"]["channels_list"])
        else:
            await message.reply("لیست کانال‌ها:\n" + "\n".join(channels))
    elif text == "اضافه کردن کانال":
        await message.reply(MENU_TEXTS["fa"]["add_channel"])
    elif text.startswith("@"):
        channels.append(text)
        await message.reply(MENU_TEXTS["fa"]["channel_added"], reply_markup=get_main_keyboard())
    elif text == "تنظیمات":
        await message.reply(MENU_TEXTS["fa"]["settings"], reply_markup=get_main_keyboard())
    elif text == "ترجمه متن":
        await message.reply(MENU_TEXTS["fa"]["translate_prompt"])
    elif text == "توقف ربات":
        await message.reply(MENU_TEXTS["fa"]["stop_bot"])
        print("Bot stopped by user")
        raise SystemExit  # ربات رو متوقف می‌کنه
    elif text == "آمار":
        await message.reply(MENU_TEXTS["fa"]["stats"], reply_markup=get_main_keyboard())
    elif "ترجمه متن" in message.reply_to_message.text if message.reply_to_message else False:
        # ترجمه ساده (بدون googletrans که پیچیده نشه)
        await message.reply(f"ترجمه (تستی): {text} -> {text} (انگلیسی)", reply_markup=get_main_keyboard())
    else:
        await message.reply(f"پیامت: {text}", reply_markup=get_main_keyboard())

def register_handlers(dp: Dispatcher):
    dp.register_message_handler(start_command, commands=["start"])
    dp.register_message_handler(handle_message, content_types=["text"])
