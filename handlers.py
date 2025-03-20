# handlers.py
from aiogram import Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from config import MASTER_ADMIN_ID, MASTER_PASSWORD, CHECK_CHANNEL, BACKUP_CHAT_ID
from database import (init_db, add_admin, get_admin, get_all_admins, add_channel, get_channels, 
                     add_destination, get_destinations, add_to_blacklist, is_blacklisted, 
                     log_action, get_logs, set_active, set_language, set_polling_interval, 
                     get_last_update, update_last_update, get_backup)
import googletrans
from googletrans import Translator
import asyncio
import os

translator = Translator()

# منوهای چندزبانه
MENU_TEXTS = {
    "fa": {
        "main_menu": ["لیست کانال‌ها", "اضافه کردن کانال", "تنظیمات", "ترجمه متن", "توقف ربات", "آمار"],
        "settings": ["تغییر زبان", "تنظیم فاصله پایش", "اضافه کردن مقصد", "قوانین", "بازگشت"],
        "master_menu": ["مدیریت ادمین‌ها", "لیست سیاه", "لاگ‌ها", "توقف گلوبال", "توقف برای ادمین خاص"],
        "super_menu": ["اضافه کردن ادمین", "حذف/ارتقا ادمین"],
        "welcome": "خوش اومدی! لطفاً از منو انتخاب کن:",
        "not_admin": "شما ادمین نیستید یا در کانال مجاز عضو نیستید!",
        "master_init": "لطفاً کلمه رمز رو بفرست تا مستر ادمین ثبت بشی:",
        "master_success": "شما به عنوان مستر ادمین ثبت شدید!",
        "add_channel": "لطفاً آیدی کانال رو بفرست (مثل @channel):",
        "add_white": "لیست سفید رو بفرست (کلمات با کاما جدا بشن):",
        "add_black": "لیست سیاه رو بفرست (کلمات با کاما جدا بشن):",
        "channel_added": "کانال اضافه شد!",
        "channel_blacklisted": "این کانال در لیست سیاهه!",
        "stats": "آمار: {channels} کانال، {messages} پیام ترجمه‌شده",
        "translate": "متنت رو بفرست تا ترجمه کنم:",
        "stop": "ربات برای شما متوقف شد!",
        "start": "ربات برای شما فعال شد!",
        "global_stop": "ربات برای همه متوقف شد!",
        "specific_stop": "آیدی ادمین رو بفرست تا ربات براش متوقف بشه:",
    },
    "en": {
        "main_menu": ["Channel List", "Add Channel", "Settings", "Translate Text", "Stop Bot", "Stats"],
        "settings": ["Change Language", "Set Polling Interval", "Add Destination", "Rules", "Back"],
        "master_menu": ["Manage Admins", "Blacklist", "Logs", "Global Stop", "Stop for Specific Admin"],
        "super_menu": ["Add Admin", "Remove/Upgrade Admin"],
        "welcome": "Welcome! Please choose from the menu:",
        "not_admin": "You’re not an admin or not in the allowed channel!",
        "master_init": "Please send the password to register as Master Admin:",
        "master_success": "You’ve been registered as Master Admin!",
        "add_channel": "Please send the channel ID (e.g., @channel):",
        "add_white": "Send the whitelist (words separated by commas):",
        "add_black": "Send the blacklist (words separated by commas):",
        "channel_added": "Channel added!",
        "channel_blacklisted": "This channel is blacklisted!",
        "stats": "Stats: {channels} channels, {messages} translated messages",
        "translate": "Send your text to translate:",
        "stop": "Bot stopped for you!",
        "start": "Bot started for you!",
        "global_stop": "Bot stopped for everyone!",
        "specific_stop": "Send the admin ID to stop the bot for them:",
    }
}

async def is_member(bot, user_id):
    try:
        member = await bot.get_chat_member(CHECK_CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        log_action(user_id, f"Error in is_member: {str(e)}")
        return False

def get_main_keyboard(admin):
    lang = admin[2] if admin else "fa"
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    for item in MENU_TEXTS[lang]["main_menu"]:
        keyboard.add(KeyboardButton(item))
    if admin and admin[1] == "master_admin":
        for item in MENU_TEXTS[lang]["master_menu"]:
            keyboard.add(KeyboardButton(item))
    elif admin and admin[1] == "super_admin":
        for item in MENU_TEXTS[lang]["super_menu"]:
            keyboard.add(KeyboardButton(item))
    return keyboard

def get_settings_keyboard(lang):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    for item in MENU_TEXTS[lang]["settings"]:
        keyboard.add(KeyboardButton(item))
    return keyboard

async def start_command(message: types.Message):
    admin = get_admin(message.from_user.id)
    if not admin and message.from_user.id == MASTER_ADMIN_ID and not get_all_admins():
        await message.reply(MENU_TEXTS["fa"]["master_init"])
        return
    if not admin or not await is_member(message.bot, message.from_user.id):
        await message.reply(MENU_TEXTS["fa"]["not_admin"])
        return
    lang = admin[2]
    await message.reply(MENU_TEXTS[lang]["welcome"], reply_markup=get_main_keyboard(admin))

async def handle_message(message: types.Message):
    admin = get_admin(message.from_user.id)
    log_action(message.from_user.id, f"Received message: {message.text}")  # لاگ اضافه شده
    if not admin or not await is_member(message.bot, message.from_user.id):
        return
    
    lang = admin[2]
    text = message.text

    # ثبت مستر ادمین اولیه
    if not get_all_admins() and message.from_user.id == MASTER_ADMIN_ID and text == MASTER_PASSWORD:
        try:
            add_admin(message.from_user.id, "master_admin")
            admin = get_admin(message.from_user.id)  # بعد از ثبت دوباره بگیر
            log_action(message.from_user.id, "Master admin registered")
            await message.reply(MENU_TEXTS[lang]["master_success"], reply_markup=get_main_keyboard(admin))
        except Exception as e:
            log_action(message.from_user.id, f"Error registering master admin: {str(e)}")
            await message.reply(f"خطا در ثبت: {str(e)}")
        return

    # منوی اصلی
    if text == MENU_TEXTS[lang]["main_menu"][0]:  # لیست کانال‌ها
        channels = get_channels(message.from_user.id)
        if channels:
            response = "\n".join([f"{ch[0]} - White: {ch[1]}, Black: {ch[2]}" for ch in channels])
        else:
            response = "هیچ کانالی ثبت نشده!"
        await message.reply(response)
    
    elif text == MENU_TEXTS[lang]["main_menu"][1]:  # اضافه کردن کانال
        await message.reply(MENU_TEXTS[lang]["add_channel"])
    
    elif text == MENU_TEXTS[lang]["main_menu"][2]:  # تنظیمات
        await message.reply("تنظیمات:", reply_markup=get_settings_keyboard(lang))
    
    elif text == MENU_TEXTS[lang]["main_menu"][3]:  # ترجمه متن
        await message.reply(MENU_TEXTS[lang]["translate"])
    
    elif text == MENU_TEXTS[lang]["main_menu"][4]:  # توقف ربات
        set_active(message.from_user.id, 0 if admin[4] else 1)
        await message.reply(MENU_TEXTS[lang]["stop"] if admin[4] else MENU_TEXTS[lang]["start"])
    
    elif text == MENU_TEXTS[lang]["main_menu"][5]:  # آمار
        channels = len(get_channels(message.from_user.id))
        messages = 0  # اینجا باید منطق شمارش پیام‌ها اضافه بشه
        await message.reply(MENU_TEXTS[lang]["stats"].format(channels=channels, messages=messages))

    # تنظیمات
    elif text == MENU_TEXTS[lang]["settings"][0]:  # تغییر زبان
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(KeyboardButton("فارسی"), KeyboardButton("English"))
        await message.reply("زبان رو انتخاب کن:", reply_markup=keyboard)
    
    elif text == MENU_TEXTS[lang]["settings"][1]:  # تنظیم فاصله پایش
        await message.reply("فاصله پایش رو به دقیقه بفرست (۱ تا ۱۵):")
    
    elif text == MENU_TEXTS[lang]["settings"][2]:  # اضافه کردن مقصد
        await message.reply("آیدی چت مقصد رو بفرست:")
    
    elif text == MENU_TEXTS[lang]["settings"][3]:  # قوانین
        await message.reply("قوانین استفاده از ربات: ...")
    
    elif text == MENU_TEXTS[lang]["settings"][4]:  # بازگشت
        await message.reply(MENU_TEXTS[lang]["welcome"], reply_markup=get_main_keyboard(admin))

    # مستر ادمین
    elif admin[1] == "master_admin" and text == MENU_TEXTS[lang]["master_menu"][1]:  # لیست سیاه
        await message.reply("آیدی کانال رو برای اضافه کردن به لیست سیاه بفرست:")
    
    elif admin[1] == "master_admin" and text == MENU_TEXTS[lang]["master_menu"][2]:  # لاگ‌ها
        logs = get_logs()
        response = "\n".join([f"Admin {log[0]}: {log[1]} at {log[2]}" for log in logs])
        await message.reply(response or "لاگی ثبت نشده!")
    
    elif admin[1] == "master_admin" and text == MENU_TEXTS[lang]["master_menu"][3]:  # توقف گلوبال
        for adm in get_all_admins():
            set_active(adm[0], 0)
        await message.reply(MENU_TEXTS[lang]["global_stop"])
    
    elif admin[1] == "master_admin" and text == MENU_TEXTS[lang]["master_menu"][4]:  # توقف برای ادمین خاص
        await message.reply(MENU_TEXTS[lang]["specific_stop"])

    # ورودی‌های متنی
    elif message.reply_to_message:
        if message.reply_to_message.text == MENU_TEXTS[lang]["add_channel"]:
            channel_id = text
            if is_blacklisted(channel_id):
                await message.reply(MENU_TEXTS[lang]["channel_blacklisted"])
            else:
                add_channel(message.from_user.id, channel_id)
                await message.reply(MENU_TEXTS[lang]["add_white"])
        
        elif message.reply_to_message.text == MENU_TEXTS[lang]["add_white"]:
            white_list = text
            channels = get_channels(message.from_user.id)[-1]
            add_channel(message.from_user.id, channels[0], white_list, channels[2])
            await message.reply(MENU_TEXTS[lang]["add_black"])
        
        elif message.reply_to_message.text == MENU_TEXTS[lang]["add_black"]:
            black_list = text
            channels = get_channels(message.from_user.id)[-1]
            add_channel(message.from_user.id, channels[0], channels[1], black_list)
            await message.reply(MENU_TEXTS[lang]["channel_added"])
        
        elif message.reply_to_message.text == MENU_TEXTS[lang]["translate"]:
            translated = translator.translate(text, dest=lang).text
            await message.reply(translated)
        
        elif message.reply_to_message.text == "فاصله پایش رو به دقیقه بفرست (۱ تا ۱۵):":
            try:
                interval = int(text) * 60
                if 60 <= interval <= 900:
                    set_polling_interval(message.from_user.id, interval)
                    await message.reply(f"فاصله پایش تنظیم شد: {text} دقیقه")
                else:
                    await message.reply("لطفاً عددی بین ۱ تا ۱۵ وارد کن!")
            except ValueError:
                await message.reply("لطفاً یه عدد معتبر بفرست!")
        
        elif message.reply_to_message.text == "آیدی چت مقصد رو بفرست:":
            add_destination(message.from_user.id, text)
            await message.reply("مقصد اضافه شد!")
        
        elif message.reply_to_message.text == "آیدی کانال رو برای اضافه کردن به لیست سیاه بفرست:":
            add_to_blacklist(text)
            await message.reply("کانال به لیست سیاه اضافه شد!")
        
        elif message.reply_to_message.text == MENU_TEXTS[lang]["specific_stop"]:
            try:
                set_active(int(text), 0)
                await message.reply(f"ربات برای ادمین {text} متوقف شد!")
            except ValueError:
                await message.reply("لطفاً یه آیدی عددی معتبر بفرست!")

    elif text in ["فارسی", "English"]:
        set_language(message.from_user.id, "fa" if text == "فارسی" else "en")
        await message.reply(f"زبان به {text} تغییر کرد!", reply_markup=get_main_keyboard(admin))

async def monitor_channels(bot):
    while True:
        admins = get_all_admins()
        if not admins:
            await asyncio.sleep(60)
            continue
        for i, (admin_id, level) in enumerate(admins):
            admin = get_admin(admin_id)
            if not admin or not admin[4]:  # اگه غیرفعاله
                continue
            channels = get_channels(admin_id)
            for channel_id, white_list, black_list in channels:
                try:
                    updates = await bot.get_updates(offset=get_last_update(channel_id))
                    for update in updates:
                        if update.channel_post and str(update.channel_post.chat.id) == channel_id:
                            text = update.channel_post.text
                            if not text:
                                continue
                            white_words = white_list.split(",") if white_list else []
                            black_words = black_list.split(",") if black_list else []
                            has_white = not white_words or any(word in text for word in white_words)
                            has_black = any(word in text for word in black_words)
                            if has_white or (not black_words and not white_words) or (has_white and has_black):
                                translated = translator.translate(text, dest=admin[2]).text
                                for dest in get_destinations(admin_id):
                                    await bot.send_message(dest, translated)
                            update_last_update(channel_id, update.update_id)
                except Exception as e:
                    log_action(admin_id, f"Error in monitoring {channel_id}: {str(e)}")
            await asyncio.sleep(12)  # ۱۲ ثانیه فاصله بین هر گروه
        await asyncio.sleep(48)  # تکمیل چرخه ۱ دقیقه‌ای

async def backup_task(bot):
    while True:
        await asyncio.sleep(3 * 24 * 60 * 60)  # هر ۳ روز
        try:
            backup_file = get_backup()
            with open(backup_file, "rb") as f:
                await bot.send_document(BACKUP_CHAT_ID, f)
            os.remove(backup_file)
        except Exception as e:
            log_action(MASTER_ADMIN_ID, f"Backup failed: {str(e)}")

def register_handlers(dp: Dispatcher):
    dp.register_message_handler(start_command, commands=["start"])
    dp.register_message_handler(handle_message, content_types=["text"])
