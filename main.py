import asyncio
from telethon import TelegramClient, events
from telethon.tl.functions.channels import JoinChannelRequest
from database import init_db, get_user_channels, get_user_settings, get_filters, is_blacklisted, log_action, get_admin_level, get_all_admins, add_admin, update_settings, add_channel, remove_channel, add_blacklist, add_filter
from googletrans import Translator
from config import CREATOR_ID, MASTER_PASSWORD

# تنظیمات اولیه Telethon
API_ID = 12345  # API ID خودت رو اینجا بذار
API_HASH = '0123456789abcdef0123456789abcdef'  # API Hash خودت رو اینجا بذار
PHONE = '+989123456789'  # شماره تلفن حساب کاربری
client = TelegramClient('session_name', API_ID, API_HASH)
translator = Translator()

# متغیرهای گلوبال برای مدیریت state
user_states = {}

# پیام‌های منو (چندزبانه)
MENU_TEXTS = {
    "fa": {
        "main_menu": ["مدیریت ادمین‌ها", "مدیریت کانال‌ها", "ترجمه متن", "توقف بات", "تنظیمات"],
        "welcome": "خوش اومدی! لطفاً از منو انتخاب کن:",
        "creator_init": "لطفاً کلمه رمز رو بفرست تا Creator ثبت بشی:",
        "creator_success": "شما به عنوان Creator ثبت شدید!",
        "not_admin": "شما ادمین نیستید!",
        "chat_destination": "لطفاً آیدی چت مقصد رو بفرست (مثلاً @username یا ID عددی):",
        "admins_menu": ["لیست ادمین‌ها", "اضافه کردن ادمین", "حذف ادمین", "ارتقا/تنزل ادمین", "بازگشت"],
        "channels_menu": ["لیست کانال‌ها", "اضافه کردن کانال", "حذف کانال", "لیست سیاه", "فیلتر کلمات", "لینک دعوت برای کانال خصوصی", "رد کردن کانال", "بازگشت"],
        "admin_list": "لیست ادمین‌ها:\n{list}",
        "add_admin_prompt": "در کدام سطح؟ مستر ادمین، سوپر ادمین یا ادمین:",
        "add_admin_id": "آیدی عددی ادمین رو بفرست:",
        "admin_added": "ادمین {user_id} در سطح {level} اضافه شد!",
        "remove_admin_id": "آیدی ادمین رو بفرست:",
        "admin_removed": "ادمین {user_id} حذف شد!",
        "promote_demote": "ادمین رو انتخاب کن:\n{list}\nسپس بگو 'ارتقا' یا 'تنزل':",
        "level_changed": "سطح {user_id} به {level} تغییر کرد!",
        "channels_list": "کانال‌های شما:\n{list}",
        "add_channel_prompt": "آیدی کانال یا پیام فورواردشده بفرست:",
        "channel_added": "کانال با موفقیت اضافه شد!",
        "remove_channel_prompt": "آیدی کانال رو بفرست:",
        "channel_removed": "کانال حذف شد!",
        "blacklist_prompt": "آیدی کانال برای لیست سیاه:",
        "blacklist_added": "کانال به لیست سیاه اضافه شد!",
        "blacklist_error": "این کانال در لیست سیاهه!",
        "limit_exceeded": "حداکثر تعداد کانال‌ها برای سطح شما: {limit}",
        "translate_prompt": "متن رو بفرست:",
        "stop_personal": "بات برای شما متوقف شد!",
        "stop_global": "بات برای همه متوقف شد!",
        "settings_menu": ["زبان اینترفیس", "زبان مقصد ترجمه", "تغییر چت مقصد", "قالب پیام دریافتی", "بازگشت"],
        "interface_lang": "زبان اینترفیس رو انتخاب کن (fa، en، ar، ru):",
        "dest_lang": "زبان مقصد ترجمه رو انتخاب کن (مثلاً en یا fr):",
        "no_access": "شما دسترسی به این کار ندارید!",
        "capacity_increased": "ظرفیت تعداد کانال‌های تحت رصد شما به {limit} افزایش یافت!",
        "channels_adjusted": "به دلیل تنزل سطح، {count} کانال آخر از لیست شما حذف شد.",
        "filter_menu": ["لیست سیاه کلمات", "لیست سفید کلمات", "بازگشت"],
        "select_channel": "کانال رو انتخاب کن:\n{list}",
        "blacklist_words": "کلمات لیست سیاه رو بفرست (با کاما جدا کن):",
        "whitelist_words": "کلمات لیست سفید رو بفرست (با کاما جدا کن):",
        "filter_added": "فیلتر برای {channel} ثبت شد!",
        "message_format": "قالب پیام رو انتخاب کن:\n1. فقط متن\n2. متن + کانال مبدا",
        "format_set": "قالب پیام به '{format}' تنظیم شد!",
        "back": "بازگشت",
        "stop_options": ["شخصی", "گلوبال", "بازگشت"],
        "error_numeric_id": "آیدی باید عدد باشه!",
        "error_invalid_format": "فرمت اشتباهه! مثلاً 'ID ارتقا' یا 'ID تنزل'",
        "error_invalid_channel": "کانال نامعتبر!",
        "error_invalid_lang": "فقط fa، en، ar، ru!",
        "error_invalid_format_choice": "فقط 1 یا 2!",
        "monitor_error": "خطا در نظارت بر کانال {channel}: {error}",
        "invite_link_prompt": "لینک دعوت کانال خصوصی رو بفرست (یا بنویس 'رد' برای رد کردن):",
        "invite_link_saved": "لینک دعوت ذخیره شد!",
        "channel_skipped": "کانال رد شد."
    },
    "en": {
        "main_menu": ["Manage Admins", "Manage Channels", "Translate Text", "Stop Bot", "Settings"],
        "welcome": "Welcome! Please choose from the menu:",
        "creator_init": "Please send the password to register as Creator:",
        "creator_success": "You are registered as Creator!",
        "not_admin": "You are not an admin!",
        "chat_destination": "Please send the destination chat ID (e.g., @username or numeric ID):",
        "admins_menu": ["List Admins", "Add Admin", "Remove Admin", "Promote/Demote Admin", "Back"],
        "channels_menu": ["List Channels", "Add Channel", "Remove Channel", "Blacklist", "Word Filters", "Invite Link for Private Channel", "Skip Channel", "Back"],
        "admin_list": "Admins list:\n{list}",
        "add_admin_prompt": "At which level? Master Admin, Super Admin, or Admin:",
        "add_admin_id": "Send the admin’s numeric ID:",
        "admin_added": "Admin {user_id} added at level {level}!",
        "remove_admin_id": "Send the admin’s ID:",
        "admin_removed": "Admin {user_id} removed!",
        "promote_demote": "Select an admin:\n{list}\nThen say 'Promote' or 'Demote':",
        "level_changed": "Level of {user_id} changed to {level}!",
        "channels_list": "Your channels:\n{list}",
        "add_channel_prompt": "Send channel ID or a forwarded message:",
        "channel_added": "Channel added successfully!",
        "remove_channel_prompt": "Send the channel ID:",
        "channel_removed": "Channel removed!",
        "blacklist_prompt": "Channel ID for blacklist:",
        "blacklist_added": "Channel added to blacklist!",
        "blacklist_error": "This channel is blacklisted!",
        "limit_exceeded": "Maximum number of channels for your level: {limit}",
        "translate_prompt": "Send the text:",
        "stop_personal": "Bot stopped for you!",
        "stop_global": "Bot stopped for everyone!",
        "settings_menu": ["Interface Language", "Translation Target Language", "Change Chat Destination", "Message Format", "Back"],
        "interface_lang": "Choose interface language (fa, en, ar, ru):",
        "dest_lang": "Choose translation target language (e.g., en or fr):",
        "no_access": "You don’t have access to this!",
        "capacity_increased": "Your channel monitoring capacity increased to {limit}!",
        "channels_adjusted": "Due to demotion, {count} last channels were removed from your list.",
        "filter_menu": ["Blacklist Words", "Whitelist Words", "Back"],
        "select_channel": "Select a channel:\n{list}",
        "blacklist_words": "Send blacklist words (comma-separated):",
        "whitelist_words": "Send whitelist words (comma-separated):",
        "filter_added": "Filter set for {channel}!",
        "message_format": "Choose message format:\n1. Text only\n2. Text + source channel",
        "format_set": "Message format set to '{format}'!",
        "back": "Back",
        "stop_options": ["Personal", "Global", "Back"],
        "error_numeric_id": "ID must be numeric!",
        "error_invalid_format": "Wrong format! E.g., 'ID Promote' or 'ID Demote'",
        "error_invalid_channel": "Invalid channel!",
        "error_invalid_lang": "Only fa, en, ar, ru!",
        "error_invalid_format_choice": "Only 1 or 2!",
        "monitor_error": "Error monitoring channel {channel}: {error}",
        "invite_link_prompt": "Send the invite link for the private channel (or type 'Skip' to skip):",
        "invite_link_saved": "Invite link saved!",
        "channel_skipped": "Channel skipped."
    },
    "ar": {
        "main_menu": ["إدارة المشرفين", "إدارة القنوات", "ترجمة النص", "إيقاف البوت", "الإعدادات"],
        "welcome": "مرحبًا! الرجاء الاختيار من القائمة:",
        "creator_init": "أرسل كلمة المرور للتسجيل كمنشئ:",
        "creator_success": "تم تسجيلك كمنشئ!",
        "not_admin": "أنت لست مشرفًا!",
        "chat_destination": "أرسل معرف الدردشة المقصودة (مثل @username أو ID رقمي):",
        "admins_menu": ["قائمة المشرفين", "إضافة مشرف", "حذف مشرف", "ترقية/تنزيل مشرف", "رجوع"],
        "channels_menu": ["قائمة القنوات", "إضافة قناة", "حذف قناة", "القائمة السوداء", "فلاتر الكلمات", "رابط دعوة لقناة خاصة", "تخطي القناة", "رجوع"],
        "admin_list": "قائمة المشرفين:\n{list}",
        "add_admin_prompt": "في أي مستوى؟ مشرف رئيسي، مشرف خارق، أو مشرف:",
        "add_admin_id": "أرسل معرف المشرف الرقمي:",
        "admin_added": "تمت إضافة المشرف {user_id} في المستوى {level}!",
        "remove_admin_id": "أرسل معرف المشرف:",
        "admin_removed": "تم حذف المشرف {user_id}!",
        "promote_demote": "اختر مشرفًا:\n{list}\nثم قل 'ترقية' أو 'تنزيل':",
        "level_changed": "تم تغيير مستوى {user_id} إلى {level}!",
        "channels_list": "قنواتك:\n{list}",
        "add_channel_prompt": "أرسل معرف القناة أو رسالة معاد توجيهها:",
        "channel_added": "تمت إضافة القناة بنجاح!",
        "remove_channel_prompt": "أرسل معرف القناة:",
        "channel_removed": "تم حذف القناة!",
        "blacklist_prompt": "معرف القناة للقائمة السوداء:",
        "blacklist_added": "تمت إضافة القناة إلى القائمة السوداء!",
        "blacklist_error": "هذه القناة في القائمة السوداء!",
        "limit_exceeded": "الحد الأقصى لعدد القنوات لمستواك: {limit}",
        "translate_prompt": "أرسل النص:",
        "stop_personal": "تم إيقاف البوت بالنسبة لك!",
        "stop_global": "تم إيقاف البوت للجميع!",
        "settings_menu": ["لغة الواجهة", "لغة الترجمة المستهدفة", "تغيير وجهة الدردشة", "تنسيق الرسالة", "رجوع"],
        "interface_lang": "اختر لغة الواجهة (fa، en، ar، ru):",
        "dest_lang": "اختر لغة الترجمة المستهدفة (مثل en أو fr):",
        "no_access": "ليس لديك صلاحية لهذا!",
        "capacity_increased": "تم زيادة سعة مراقبة القنوات الخاصة بك إلى {limit}!",
        "channels_adjusted": "بسبب التنزيل، تم حذف {count} قنوات أخيرة من قائمتك.",
        "filter_menu": ["كلمات القائمة السوداء", "كلمات القائمة البيضاء", "رجوع"],
        "select_channel": "اختر قناة:\n{list}",
        "blacklist_words": "أرسل كلمات القائمة السوداء (مفصولة بفواصل):",
        "whitelist_words": "أرسل كلمات القائمة البيضاء (مفصولة بفواصل):",
        "filter_added": "تم تعيين الفلتر لـ {channel}!",
        "message_format": "اختر تنسيق الرسالة:\n1. النص فقط\n2. النص + قناة المصدر",
        "format_set": "تم تعيين تنسيق الرسالة إلى '{format}'!",
        "back": "رجوع",
        "stop_options": ["شخصي", "عام", "رجوع"],
        "error_numeric_id": "المعرف يجب أن يكون رقميًا!",
        "error_invalid_format": "صيغة خاطئة! مثل 'ID ترقية' أو 'ID تنزيل'",
        "error_invalid_channel": "قناة غير صالحة!",
        "error_invalid_lang": "فقط fa، en، ar، ru!",
        "error_invalid_format_choice": "فقط 1 أو 2!",
        "monitor_error": "خطأ في مراقبة القناة {channel}: {error}",
        "invite_link_prompt": "أرسل رابط الدعوة للقناة الخاصة (أو اكتب 'تخطي' للتخطي):",
        "invite_link_saved": "تم حفظ رابط الدعوة!",
        "channel_skipped": "تم تخطي القناة."
    },
    "ru": {
        "main_menu": ["Управление админами", "Управление каналами", "Перевод текста", "Остановить бота", "Настройки"],
        "welcome": "Добро пожаловать! Выберите из меню:",
        "creator_init": "Отправьте пароль для регистрации как Создатель:",
        "creator_success": "Вы зарегистрированы как Создатель!",
        "not_admin": "Вы не администратор!",
        "chat_destination": "Отправьте ID целевого чата (например, @username или числовой ID):",
        "admins_menu": ["Список админов", "Добавить админа", "Удалить админа", "Повысить/понизить админа", "Назад"],
        "channels_menu": ["Список каналов", "Добавить канал", "Удалить канал", "Черный список", "Фильтры слов", "Пригласительная ссылка для частного канала", "Пропустить канал", "Назад"],
        "admin_list": "Список админов:\n{list}",
        "add_admin_prompt": "На каком уровне? Мастер-админ, Супер-админ или Админ:",
        "add_admin_id": "Отправьте числовой ID админа:",
        "admin_added": "Админ {user_id} добавлен на уровень {level}!",
        "remove_admin_id": "Отправьте ID админа:",
        "admin_removed": "Админ {user_id} удален!",
        "promote_demote": "Выберите админа:\n{list}\nЗатем скажите 'Повысить' или 'Понизить':",
        "level_changed": "Уровень {user_id} изменен на {level}!",
        "channels_list": "Ваши каналы:\n{list}",
        "add_channel_prompt": "Отправьте ID канала или пересланное сообщение:",
        "channel_added": "Канал успешно добавлен!",
        "remove_channel_prompt": "Отправьте ID канала:",
        "channel_removed": "Канал удален!",
        "blacklist_prompt": "ID канала для черного списка:",
        "blacklist_added": "Канал добавлен в черный список!",
        "blacklist_error": "Этот канал в черном списке!",
        "limit_exceeded": "Максимальное количество каналов для вашего уровня: {limit}",
        "translate_prompt": "Отправьте текст:",
        "stop_personal": "Бот остановлен для вас!",
        "stop_global": "Бот остановлен для всех!",
        "settings_menu": ["Язык интерфейса", "Язык перевода", "Изменить целевой чат", "Формат сообщения", "Назад"],
        "interface_lang": "Выберите язык интерфейса (fa, en, ar, ru):",
        "dest_lang": "Выберите язык перевода (например, en или fr):",
        "no_access": "У вас нет доступа к этому!",
        "capacity_increased": "Ваша емкость мониторинга каналов увеличена до {limit}!",
        "channels_adjusted": "Из-за понижения уровня {count} последних каналов удалены из вашего списка.",
        "filter_menu": ["Черный список слов", "Белый список слов", "Назад"],
        "select_channel": "Выберите канал:\n{list}",
        "blacklist_words": "Отправьте слова черного списка (через запятую):",
        "whitelist_words": "Отправьте слова белого списка (через запятую):",
        "filter_added": "Фильтр установлен для {channel}!",
        "message_format": "Выберите формат сообщения:\n1. Только текст\n2. Текст + канал-источник",
        "format_set": "Формат сообщения установлен на '{format}'!",
        "back": "Назад",
        "stop_options": ["Лично", "Глобально", "Назад"],
        "error_numeric_id": "ID должен быть числовым!",
        "error_invalid_format": "Неверный формат! Например, 'ID Повысить' или 'ID Понизить'",
        "error_invalid_channel": "Недействительный канал!",
        "error_invalid_lang": "Только fa, en, ar, ru!",
        "error_invalid_format_choice": "Только 1 или 2!",
        "monitor_error": "Ошибка мониторинга канала {channel}: {error}",
        "invite_link_prompt": "Отправьте пригласительную ссылку для частного канала (или напишите 'Пропустить' для пропуска):",
        "invite_link_saved": "Пригласительная ссылка сохранена!",
        "channel_skipped": "Канал пропущен."
    }
}

# تابع برای ساخت منو
def get_main_menu_text(level, lang="fa"):
    menu = MENU_TEXTS[lang]["main_menu"].copy()
    if level != 1:
        menu[3] = f"{MENU_TEXTS[lang]['main_menu'][3]} (شخصی)" if lang == "fa" else f"{MENU_TEXTS[lang]['main_menu'][3]} (Personal)"
    return "\n".join(menu)

def get_submenu_text(menu_items, lang="fa"):
    return "\n".join(menu_items)

# تابع برای ارسال پیام به چت مقصد
async def send_to_destination(admin_id, channel, translated_text, message, settings):
    message_content = translated_text if settings["message_format"] == "text_only" else f"{translated_text}\nاز {channel}" if settings["interface_lang"] == "fa" else f"{translated_text}\nFrom {channel}"
    await client.send_message(settings["chat_destination"], message_content)
    log_action(admin_id, f"Sent translated text from {channel}")

    if message.photo or message.video or message.audio or message.voice:
        await client.forward_messages(settings["chat_destination"], message.message_id, message.chat_id)
        log_action(admin_id, f"Forwarded media from {channel}")

# هندل کردن پیام‌های جدید از کانال‌ها
@client.on(events.NewMessage)
async def handle_new_message(event):
    channel = f"@{event.chat.username}" if event.chat.username else str(event.chat_id)
    admin_id = None
    for uid in get_all_admins():
        if channel in get_user_channels(uid):
            admin_id = uid
            break
    if not admin_id:
        return

    settings = get_user_settings(admin_id)
    lang = settings["interface_lang"]
    if not settings["chat_destination"] or settings["stopped"]:
        return

    if is_blacklisted(channel):
        return

    news_text = event.message.text or event.message.caption or "بدون متن" if lang == "fa" else "No text"
    translated = translator.translate(news_text, dest=settings["dest_lang"]).text.lower()

    filters = get_filters(admin_id, channel)
    blacklist = filters["blacklist"].split(",") if filters["blacklist"] else []
    whitelist = filters["whitelist"].split(",") if filters["whitelist"] else []

    should_send = True
    has_black = blacklist and any(word.strip() in translated for word in blacklist)
    has_white = whitelist and any(word.strip() in translated for word in whitelist)

    if blacklist and whitelist:
        should_send = has_white or not has_black
    elif blacklist:
        should_send = not has_black
    elif whitelist:
        should_send = has_white

    if should_send:
        await send_to_destination(admin_id, channel, translated, event.message, settings)

    await asyncio.sleep(0.2)  # تأخیر کمتر برای جلوگیری از اسپم

# هندل کردن پیام‌های ادمین‌ها
@client.on(events.NewMessage)
async def handle_admin_message(event):
    user_id = event.sender_id
    text = event.message.text
    level = get_admin_level(user_id)
    log_action(user_id, f"Received: {text}")

    # ثبت سازنده (Creator)
    if not level and user_id == CREATOR_ID and text == MASTER_PASSWORD:
        add_admin(user_id, 1)
        await event.reply(MENU_TEXTS["fa"]["creator_success"])
        await event.reply(MENU_TEXTS["fa"]["chat_destination"])
        log_action(user_id, "Creator registered")
        user_states[user_id] = "awaiting_chat_destination"
        return

    if not level:
        await event.reply(MENU_TEXTS["fa"]["not_admin"])
        return

    settings = get_user_settings(user_id)
    lang = settings["interface_lang"]

    # تنظیم چت مقصد
    if user_states.get(user_id) == "awaiting_chat_destination":
        update_settings(user_id, chat_destination=text)
        await event.reply(MENU_TEXTS[lang]["welcome"])
        await event.reply(get_main_menu_text(level, lang))
        user_states[user_id] = "main_menu"
        return

    # منوی اصلی
    if text == "/start" or user_states.get(user_id) == "main_menu":
        if not settings["chat_destination"]:
            await event.reply(MENU_TEXTS[lang]["chat_destination"])
            user_states[user_id] = "awaiting_chat_destination"
            return
        await event.reply(MENU_TEXTS[lang]["welcome"])
        await event.reply(get_main_menu_text(level, lang))
        user_states[user_id] = "main_menu"
        return

    # مدیریت ادمین‌ها
    if text == MENU_TEXTS[lang]["main_menu"][0] and level in [1, 2, 3]:
        admins_menu = MENU_TEXTS[lang]["admins_menu"]
        if level != 1:
            admins_menu = [item for item in admins_menu if item != MENU_TEXTS[lang]["admins_menu"][2]]
            if level != 2:
                admins_menu = [item for item in admins_menu if item != MENU_TEXTS[lang]["admins_menu"][3]]
        await event.reply(MENU_TEXTS[lang]["admins_menu"][0].split()[0] + ":")
        await event.reply(get_submenu_text(admins_menu, lang))
        user_states[user_id] = "admins_menu"
    elif user_states.get(user_id) == "admins_menu":
        if text == MENU_TEXTS[lang]["admins_menu"][0]:
            admins = get_all_admins()
            admin_list = "\n".join([f"{uid} - سطح {get_admin_level(uid)}" if lang == "fa" else f"{uid} - Level {get_admin_level(uid)}" for uid in admins])
            await event.reply(MENU_TEXTS[lang]["admin_list"].format(list=admin_list))
            await event.reply(get_submenu_text(MENU_TEXTS[lang]["admins_menu"], lang))
        elif text == MENU_TEXTS[lang]["admins_menu"][1]:
            await event.reply(MENU_TEXTS[lang]["add_admin_prompt"])
            user_states[user_id] = "awaiting_admin_level"
        elif text in [MENU_TEXTS[lang]["admins_menu"][1].split()[2], MENU_TEXTS[lang]["admins_menu"][1].split()[3], MENU_TEXTS[lang]["admins_menu"][1].split()[4]] and user_states.get(user_id) == "awaiting_admin_level":
            level_map = {MENU_TEXTS[lang]["admins_menu"][1].split()[2]: 2, MENU_TEXTS[lang]["admins_menu"][1].split()[3]: 3, MENU_TEXTS[lang]["admins_menu"][1].split()[4]: 4}
            if level == 2 and level_map[text] <= 2 or level == 3 and level_map[text] <= 3:
                await event.reply(MENU_TEXTS[lang]["no_access"])
                await event.reply(get_submenu_text(MENU_TEXTS[lang]["admins_menu"], lang))
                return
            await event.reply(MENU_TEXTS[lang]["add_admin_id"])
            update_settings(user_id, pending_level=level_map[text])
            user_states[user_id] = "awaiting_admin_id"
        elif user_states.get(user_id) == "awaiting_admin_id":
            try:
                new_admin_id = int(text)
                add_admin(new_admin_id, settings["pending_level"])
                await event.reply(MENU_TEXTS[lang]["admin_added"].format(user_id=new_admin_id, level=settings["pending_level"]))
                await event.reply(get_submenu_text(MENU_TEXTS[lang]["admins_menu"], lang))
                log_action(user_id, f"Added admin {new_admin_id} at level {settings['pending_level']}")
                user_states[user_id] = "admins_menu"
            except ValueError:
                await event.reply(MENU_TEXTS[lang]["error_numeric_id"])
                await event.reply(get_submenu_text(MENU_TEXTS[lang]["admins_menu"], lang))
        elif text == MENU_TEXTS[lang]["admins_menu"][2] and level == 1:
            await event.reply(MENU_TEXTS[lang]["remove_admin_id"])
            user_states[user_id] = "awaiting_remove_admin_id"
        elif user_states.get(user_id) == "awaiting_remove_admin_id":
            try:
                remove_id = int(text)
                add_admin(remove_id, None)
                await event.reply(MENU_TEXTS[lang]["admin_removed"].format(user_id=remove_id))
                await event.reply(get_submenu_text(MENU_TEXTS[lang]["admins_menu"], lang))
                log_action(user_id, f"Removed admin {remove_id}")
                user_states[user_id] = "admins_menu"
            except ValueError:
                await event.reply(MENU_TEXTS[lang]["error_numeric_id"])
                await event.reply(get_submenu_text(MENU_TEXTS[lang]["admins_menu"], lang))
        elif text == MENU_TEXTS[lang]["admins_menu"][3] and level in [1, 2]:
            admins = get_all_admins()
            admin_list = "\n".join([f"{uid} - سطح {get_admin_level(uid)}" if lang == "fa" else f"{uid} - Level {get_admin_level(uid)}" for uid in admins if level == 1 or get_admin_level(uid) > 2])
            await event.reply(MENU_TEXTS[lang]["promote_demote"].format(list=admin_list))
            user_states[user_id] = "awaiting_promote_demote"
        elif user_states.get(user_id) == "awaiting_promote_demote":
            try:
                parts = text.split()
                admin_id = int(parts[0])
                action = parts[1] if len(parts) > 1 else ""
                current_level = get_admin_level(admin_id)
                if level == 2 and current_level <= 2:
                    await event.reply(MENU_TEXTS[lang]["no_access"])
                    await event.reply(get_submenu_text(MENU_TEXTS[lang]["admins_menu"], lang))
                    return
                limits = {1: 20, 2: 20, 3: 15, 4: 10}
                if action in ["ارتقا", "Promote", "ترقية", "Повысить"] and current_level > 1:
                    new_level = current_level - 1
                    add_admin(admin_id, new_level)
                    await event.reply(MENU_TEXTS[lang]["level_changed"].format(user_id=admin_id, level=new_level))
                    await event.reply(get_submenu_text(MENU_TEXTS[lang]["admins_menu"], lang))
                    await client.send_message(admin_id, MENU_TEXTS[lang]["capacity_increased"].format(limit=limits[new_level]))
                    log_action(user_id, f"Promoted {admin_id} to level {new_level}")
                elif action in ["تنزل", "Demote", "تنزيل", "Понизить"] and current_level < 4:
                    new_level = current_level + 1
                    removed_count = adjust_channels_on_demote(admin_id, new_level)
                    add_admin(admin_id, new_level)
                    await event.reply(MENU_TEXTS[lang]["level_changed"].format(user_id=admin_id, level=new_level))
                    await event.reply(get_submenu_text(MENU_TEXTS[lang]["admins_menu"], lang))
                    if removed_count:
                        await client.send_message(admin_id, MENU_TEXTS[lang]["channels_adjusted"].format(count=removed_count))
                    log_action(user_id, f"Demoted {admin_id} to level {new_level}")
                else:
                    await event.reply(MENU_TEXTS[lang]["error_invalid_format"])
                    await event.reply(get_submenu_text(MENU_TEXTS[lang]["admins_menu"], lang))
                user_states[user_id] = "admins_menu"
            except (ValueError, IndexError):
                await event.reply(MENU_TEXTS[lang]["error_invalid_format"])
                await event.reply(get_submenu_text(MENU_TEXTS[lang]["admins_menu"], lang))
        elif text == MENU_TEXTS[lang]["admins_menu"][4]:
            await event.reply(MENU_TEXTS[lang]["welcome"])
            await event.reply(get_main_menu_text(level, lang))
            user_states[user_id] = "main_menu"

    # مدیریت کانال‌ها
    elif text == MENU_TEXTS[lang]["main_menu"][1]:
        channels_menu = MENU_TEXTS[lang]["channels_menu"]
        if level != 1:
            channels_menu = [item for item in channels_menu if item != MENU_TEXTS[lang]["channels_menu"][3]]
        await event.reply(MENU_TEXTS[lang]["channels_menu"][0].split()[0] + ":")
        await event.reply(get_submenu_text(channels_menu, lang))
        user_states[user_id] = "channels_menu"
    elif user_states.get(user_id) == "channels_menu":
        if text == MENU_TEXTS[lang]["channels_menu"][0]:
            channels = get_user_channels(user_id)
            await event.reply(MENU_TEXTS[lang]["channels_list"].format(list="\n".join(channels) if channels else "خالی" if lang == "fa" else "Empty"))
            await event.reply(get_submenu_text(MENU_TEXTS[lang]["channels_menu"], lang))
        elif text == MENU_TEXTS[lang]["channels_menu"][1]:
            await event.reply(MENU_TEXTS[lang]["add_channel_prompt"])
            user_states[user_id] = "awaiting_channel_id"
        elif user_states.get(user_id) == "awaiting_channel_id":
            channel_id = text
            if is_blacklisted(channel_id):
                await event.reply(MENU_TEXTS[lang]["blacklist_error"])
                await event.reply(get_submenu_text(MENU_TEXTS[lang]["channels_menu"], lang))
                return
            limits = {1: 20, 2: 20, 3: 15, 4: 10}
            if len(get_user_channels(user_id)) >= limits[level]:
                await event.reply(MENU_TEXTS[lang]["limit_exceeded"].format(limit=limits[level]))
                await event.reply(get_submenu_text(MENU_TEXTS[lang]["channels_menu"], lang))
                return
            try:
                await client.get_entity(channel_id)
                add_channel(user_id, channel_id)
                await event.reply(MENU_TEXTS[lang]["channel_added"])
                await event.reply(get_submenu_text(MENU_TEXTS[lang]["channels_menu"], lang))
                log_action(user_id, f"Added channel {channel_id}")
            except ValueError as e:
                if "Cannot find any entity" in str(e):
                    await event.reply(MENU_TEXTS[lang]["invite_link_prompt"])
                    user_states[user_id] = "awaiting_invite_link"
                else:
                    await event.reply(MENU_TEXTS[lang]["error_invalid_channel"])
                    await event.reply(get_submenu_text(MENU_TEXTS[lang]["channels_menu"], lang))
            user_states[user_id] = "channels_menu"
        elif text == MENU_TEXTS[lang]["channels_menu"][2]:
            await event.reply(MENU_TEXTS[lang]["remove_channel_prompt"])
            user_states[user_id] = "awaiting_remove_channel"
        elif user_states.get(user_id) == "awaiting_remove_channel":
            remove_channel(user_id, text)
            await event.reply(MENU_TEXTS[lang]["channel_removed"])
            await event.reply(get_submenu_text(MENU_TEXTS[lang]["channels_menu"], lang))
            log_action(user_id, f"Removed channel {text}")
            user_states[user_id] = "channels_menu"
        elif text == MENU_TEXTS[lang]["channels_menu"][3] and level == 1:
            await event.reply(MENU_TEXTS[lang]["blacklist_prompt"])
            user_states[user_id] = "awaiting_blacklist"
        elif user_states.get(user_id) == "awaiting_blacklist":
            add_blacklist(text)
            await event.reply(MENU_TEXTS[lang]["blacklist_added"])
            await event.reply(get_submenu_text(MENU_TEXTS[lang]["channels_menu"], lang))
            log_action(user_id, f"Blacklisted channel {text}")
            user_states[user_id] = "channels_menu"
        elif text == MENU_TEXTS[lang]["channels_menu"][4]:
            channels = get_user_channels(user_id)
            await event.reply(MENU_TEXTS[lang]["select_channel"].format(list="\n".join(channels)))
            user_states[user_id] = "awaiting_filter_channel"
        elif user_states.get(user_id) == "awaiting_filter_channel":
            if text in get_user_channels(user_id):
                update_settings(user_id, pending_channel=text)
                await event.reply(MENU_TEXTS[lang]["filter_menu"][0].split()[0] + ":")
                await event.reply(get_submenu_text(MENU_TEXTS[lang]["filter_menu"], lang))
                user_states[user_id] = "filter_menu"
            else:
                await event.reply(MENU_TEXTS[lang]["error_invalid_channel"])
                await event.reply(get_submenu_text(MENU_TEXTS[lang]["channels_menu"], lang))
        elif user_states.get(user_id) == "filter_menu":
            if text == MENU_TEXTS[lang]["filter_menu"][0]:
                await event.reply(MENU_TEXTS[lang]["blacklist_words"])
                user_states[user_id] = "awaiting_blacklist_words"
            elif text == MENU_TEXTS[lang]["filter_menu"][1]:
                await event.reply(MENU_TEXTS[lang]["whitelist_words"])
                user_states[user_id] = "awaiting_whitelist_words"
            elif user_states.get(user_id) == "awaiting_blacklist_words":
                add_filter(user_id, settings["pending_channel"], blacklist=text, whitelist=get_filters(user_id, settings["pending_channel"])["whitelist"])
                await event.reply(MENU_TEXTS[lang]["filter_added"].format(channel=settings["pending_channel"]))
                await event.reply(get_submenu_text(MENU_TEXTS[lang]["filter_menu"], lang))
                log_action(user_id, f"Set blacklist for {settings['pending_channel']}: {text}")
                user_states[user_id] = "filter_menu"
            elif user_states.get(user_id) == "awaiting_whitelist_words":
                add_filter(user_id, settings["pending_channel"], blacklist=get_filters(user_id, settings["pending_channel"])["blacklist"], whitelist=text)
                await event.reply(MENU_TEXTS[lang]["filter_added"].format(channel=settings["pending_channel"]))
                await event.reply(get_submenu_text(MENU_TEXTS[lang]["filter_menu"], lang))
                log_action(user_id, f"Set whitelist for {settings['pending_channel']}: {text}")
                user_states[user_id] = "filter_menu"
            elif text == MENU_TEXTS[lang]["filter_menu"][2]:
                await event.reply(MENU_TEXTS[lang]["channels_menu"][0].split()[0] + ":")
                await event.reply(get_submenu_text(MENU_TEXTS[lang]["channels_menu"], lang))
                user_states[user_id] = "channels_menu"
        elif text == MENU_TEXTS[lang]["channels_menu"][5]:
            await event.reply(MENU_TEXTS[lang]["invite_link_prompt"])
            user_states[user_id] = "awaiting_invite_link"
        elif user_states.get(user_id) == "awaiting_invite_link":
            if text.lower() in ["رد", "skip", "تخطي", "пропустить"]:
                await event.reply(MENU_TEXTS[lang]["channel_skipped"])
                await event.reply(get_submenu_text(MENU_TEXTS[lang]["channels_menu"], lang))
                user_states[user_id] = "channels_menu"
            else:
                update_settings(user_id, invite_link=text)
                try:
                    await client(JoinChannelRequest(text))
                    await event.reply(MENU_TEXTS[lang]["invite_link_saved"])
                    await event.reply(get_submenu_text(MENU_TEXTS[lang]["channels_menu"], lang))
                    log_action(user_id, f"Joined channel using invite link: {text}")
                except Exception as e:
                    await event.reply(f"خطا در پیوستن به کانال: {str(e)}")
                    await event.reply(get_submenu_text(MENU_TEXTS[lang]["channels_menu"], lang))
                user_states[user_id] = "channels_menu"
        elif text == MENU_TEXTS[lang]["channels_menu"][6]:
            await event.reply(MENU_TEXTS[lang]["channel_skipped"])
            await event.reply(get_submenu_text(MENU_TEXTS[lang]["channels_menu"], lang))
            user_states[user_id] = "channels_menu"
        elif text == MENU_TEXTS[lang]["channels_menu"][7]:
            await event.reply(MENU_TEXTS[lang]["welcome"])
            await event.reply(get_main_menu_text(level, lang))
            user_states[user_id] = "main_menu"

    # ترجمه متن
    elif text == MENU_TEXTS[lang]["main_menu"][2]:
        await event.reply(MENU_TEXTS[lang]["translate_prompt"])
        user_states[user_id] = "awaiting_text_to_translate"
    elif user_states.get(user_id) == "awaiting_text_to_translate":
        translated = translator.translate(text, dest=settings["dest_lang"]).text
        await event.reply(f"ترجمه: {translated}" if lang == "fa" else f"Translation: {translated}")
        await event.reply(get_main_menu_text(level, lang))
        log_action(user_id, f"Translated text: {text}")
        user_states[user_id] = "main_menu"

    # توقف بات
    elif text == MENU_TEXTS[lang]["main_menu"][3] and level == 1:
        await event.reply("شخصی یا گلوبال؟" if lang == "fa" else "Personal or Global?")
        await event.reply(get_submenu_text(MENU_TEXTS[lang]["stop_options"], lang))
        user_states[user_id] = "stop_menu"
    elif user_states.get(user_id) == "stop_menu":
        if text in [f"{MENU_TEXTS[lang]['main_menu'][3]} (شخصی)", f"{MENU_TEXTS[lang]['main_menu'][3]} (Personal)"] or text == MENU_TEXTS[lang]["stop_options"][0]:
            update_settings(user_id, stopped=True)
            await event.reply(MENU_TEXTS[lang]["stop_personal"])
            await event.reply(get_main_menu_text(level, lang))
            log_action(user_id, "Bot stopped personally")
            user_states[user_id] = "main_menu"
        elif text == MENU_TEXTS[lang]["stop_options"][1] and level == 1:
            await event.reply(MENU_TEXTS[lang]["stop_global"])
            log_action(user_id, "Bot stopped globally")
            raise SystemExit
        elif text == MENU_TEXTS[lang]["stop_options"][2]:
            await event.reply(MENU_TEXTS[lang]["welcome"])
            await event.reply(get_main_menu_text(level, lang))
            user_states[user_id] = "main_menu"

    # تنظیمات
    elif text == MENU_TEXTS[lang]["main_menu"][4]:
        await event.reply(MENU_TEXTS[lang]["settings_menu"][0].split()[0] + ":")
        await event.reply(get_submenu_text(MENU_TEXTS[lang]["settings_menu"], lang))
        user_states[user_id] = "settings_menu"
    elif user_states.get(user_id) == "settings_menu":
        if text == MENU_TEXTS[lang]["settings_menu"][0]:
            await event.reply(MENU_TEXTS[lang]["interface_lang"])
            user_states[user_id] = "awaiting_interface_lang"
        elif user_states.get(user_id) == "awaiting_interface_lang":
            if text in ["fa", "en", "ar", "ru"]:
                update_settings(user_id, interface_lang=text)
                await event.reply(f"زبان اینترفیس به {text} تغییر کرد!" if lang == "fa" else f"Interface language changed to {text}!")
                await event.reply(get_submenu_text(MENU_TEXTS[lang]["settings_menu"], lang))
                log_action(user_id, f"Interface language changed to {text}")
            else:
                await event.reply(MENU_TEXTS[lang]["error_invalid_lang"])
                await event.reply(get_submenu_text(MENU_TEXTS[lang]["settings_menu"], lang))
            user_states[user_id] = "settings_menu"
        elif text == MENU_TEXTS[lang]["settings_menu"][1]:
            await event.reply(MENU_TEXTS[lang]["dest_lang"])
            user_states[user_id] = "awaiting_dest_lang"
        elif user_states.get(user_id) == "awaiting_dest_lang":
            update_settings(user_id, dest_lang=text)
            await event.reply(f"زبان مقصد به {text} تغییر کرد!" if lang == "fa" else f"Target language changed to {text}!")
            await event.reply(get_submenu_text(MENU_TEXTS[lang]["settings_menu"], lang))
            log_action(user_id, f"Destination language changed to {text}")
            user_states[user_id] = "settings_menu"
        elif text == MENU_TEXTS[lang]["settings_menu"][2]:
            await event.reply(MENU_TEXTS[lang]["chat_destination"])
            user_states[user_id] = "awaiting_new_chat_destination"
        elif user_states.get(user_id) == "awaiting_new_chat_destination":
            update_settings(user_id, chat_destination=text)
            await event.reply(f"چت مقصد به {text} تغییر کرد!" if lang == "fa" else f"Chat destination changed to {text}!")
            await event.reply(get_submenu_text(MENU_TEXTS[lang]["settings_menu"], lang))
            log_action(user_id, f"Chat destination changed to {text}")
            user_states[user_id] = "settings_menu"
        elif text == MENU_TEXTS[lang]["settings_menu"][3]:
            await event.reply(MENU_TEXTS[lang]["message_format"])
            user_states[user_id] = "awaiting_message_format"
        elif user_states.get(user_id) == "awaiting_message_format":
            if text in ["1", "2"]:
                format_map = {"1": "text_only", "2": "text_with_source"}
                update_settings(user_id, message_format=format_map[text])
                await event.reply(MENU_TEXTS[lang]["format_set"].format(format="فقط متن" if text == "1" and lang == "fa" else "متن + کانال مبدا" if text == "2" and lang == "fa" else "Text only" if text == "1" and lang == "en" else "Text + source channel" if text == "2" and lang == "en"))
                await event.reply(get_submenu_text(MENU_TEXTS[lang]["settings_menu"], lang))
                log_action(user_id, f"Message format set to {format_map[text]}")
            else:
                await event.reply(MENU_TEXTS[lang]["error_invalid_format_choice"])
                await event.reply(get_submenu_text(MENU_TEXTS[lang]["settings_menu"], lang))
            user_states[user_id] = "settings_menu"
        elif text == MENU_TEXTS[lang]["settings_menu"][4]:
            await event.reply(MENU_TEXTS[lang]["welcome"])
            await event.reply(get_main_menu_text(level, lang))
            user_states[user_id] = "main_menu"

# تابع برای مدیریت درخواست‌ها و جلوگیری از flood
async def safe_request(coro, max_retries=3, delay=5):
    for attempt in range(max_retries):
        try:
            return await coro
        except Exception as e:
            if "FloodWaitError" in str(e):
                wait_time = int(str(e).split("A wait of ")[1].split(" seconds")[0])
                print(f"Flood wait for {wait_time} seconds")
                await asyncio.sleep(wait_time + 1)
            elif attempt == max_retries - 1:
                print(f"Error after {max_retries} attempts: {e}")
                raise
            else:
                await asyncio.sleep(delay)

# شروع برنامه
async def main():
    init_db()
    await client.start(phone=PHONE)
    print("اتصال برقرار شد!")
    await client.run_until_disconnected()

if __name__ == "__main__":
    client.loop.run_until_complete(main())