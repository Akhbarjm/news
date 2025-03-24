import asyncio
from telethon import events
from telethon.tl.functions.channels import JoinChannelRequest
from googletrans import Translator
from config import CREATOR_ID, MASTER_PASSWORD, USER_STATES, MENU_TEXTS
from database import (init_db, get_user_channels, get_user_settings, get_filters, is_blacklisted,
                     log_action, get_admin_level, get_all_admins, add_admin, update_settings,
                     add_channel, remove_channel, add_blacklist, add_filter, adjust_channels_on_demote)

translator = Translator()

def get_main_menu_text(level, lang="fa"):
    menu = MENU_TEXTS[lang]["main_menu"].copy()
    if level != 1:
        menu[3] = f"{MENU_TEXTS[lang]['main_menu'][3]} (شخصی)" if lang == "fa" else f"{MENU_TEXTS[lang]['main_menu'][3]} (Personal)"
    return "\n".join(menu)

def get_submenu_text(menu_items, lang="fa"):
    return "\n".join(menu_items)

async def send_to_destination(client, admin_id, channel, translated_text, message, settings):
    message_content = translated_text if settings["message_format"] == "text_only" else f"{translated_text}\nاز {channel}" if settings["interface_lang"] == "fa" else f"{translated_text}\nFrom {channel}"
    await client.send_message(settings["chat_destination"], message_content)
    log_action(admin_id, f"Sent translated text from {channel}")

    if message.photo or message.video or message.audio or message.voice:
        await client.forward_messages(settings["chat_destination"], message.message_id, message.chat_id)
        log_action(admin_id, f"Forwarded media from {channel}")

async def handle_new_message(event, client):
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
        await send_to_destination(client, admin_id, channel, translated, event.message, settings)

    await asyncio.sleep(0.2)  # تأخیر کمتر برای جلوگیری از اسپم

async def handle_admin_message(event, client):
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
        USER_STATES[user_id] = "awaiting_chat_destination"
        return

    if not level:
        await event.reply(MENU_TEXTS["fa"]["not_admin"])
        return

    settings = get_user_settings(user_id)
    lang = settings["interface_lang"]

    # تنظیم چت مقصد
    if USER_STATES.get(user_id) == "awaiting_chat_destination":
        update_settings(user_id, chat_destination=text)
        await event.reply(MENU_TEXTS[lang]["welcome"])
        await event.reply(get_main_menu_text(level, lang))
        USER_STATES[user_id] = "main_menu"
        return

    # منوی اصلی
    if text == "/start" or USER_STATES.get(user_id) == "main_menu":
        if not settings["chat_destination"]:
            await event.reply(MENU_TEXTS[lang]["chat_destination"])
            USER_STATES[user_id] = "awaiting_chat_destination"
            return
        await event.reply(MENU_TEXTS[lang]["welcome"])
        await event.reply(get_main_menu_text(level, lang))
        USER_STATES[user_id] = "main_menu"
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
        USER_STATES[user_id] = "admins_menu"
    elif USER_STATES.get(user_id) == "admins_menu":
        if text == MENU_TEXTS[lang]["admins_menu"][0]:
            admins = get_all_admins()
            admin_list = "\n".join([f"{uid} - سطح {get_admin_level(uid)}" if lang == "fa" else f"{uid} - Level {get_admin_level(uid)}" for uid in admins])
            await event.reply(MENU_TEXTS[lang]["admin_list"].format(list=admin_list))
            await event.reply(get_submenu_text(MENU_TEXTS[lang]["admins_menu"], lang))
        elif text == MENU_TEXTS[lang]["admins_menu"][1]:
            await event.reply(MENU_TEXTS[lang]["add_admin_prompt"])
            USER_STATES[user_id] = "awaiting_admin_level"
        elif text in [MENU_TEXTS[lang]["admins_menu"][1].split()[2], MENU_TEXTS[lang]["admins_menu"][1].split()[3], MENU_TEXTS[lang]["admins_menu"][1].split()[4]] and USER_STATES.get(user_id) == "awaiting_admin_level":
            level_map = {MENU_TEXTS[lang]["admins_menu"][1].split()[2]: 2, MENU_TEXTS[lang]["admins_menu"][1].split()[3]: 3, MENU_TEXTS[lang]["admins_menu"][1].split()[4]: 4}
            if level == 2 and level_map[text] <= 2 or level == 3 and level_map[text] <= 3:
                await event.reply(MENU_TEXTS[lang]["no_access"])
                await event.reply(get_submenu_text(MENU_TEXTS[lang]["admins_menu"], lang))
                return
            await event.reply(MENU_TEXTS[lang]["add_admin_id"])
            update_settings(user_id, pending_level=level_map[text])
            USER_STATES[user_id] = "awaiting_admin_id"
        elif USER_STATES.get(user_id) == "awaiting_admin_id":
            try:
                new_admin_id = int(text)
                add_admin(new_admin_id, settings["pending_level"])
                await event.reply(MENU_TEXTS[lang]["admin_added"].format(user_id=new_admin_id, level=settings["pending_level"]))
                await event.reply(get_submenu_text(MENU_TEXTS[lang]["admins_menu"], lang))
                log_action(user_id, f"Added admin {new_admin_id} at level {settings['pending_level']}")
                USER_STATES[user_id] = "admins_menu"
            except ValueError:
                await event.reply(MENU_TEXTS[lang]["error_numeric_id"])
                await event.reply(get_submenu_text(MENU_TEXTS[lang]["admins_menu"], lang))
        elif text == MENU_TEXTS[lang]["admins_menu"][2] and level == 1:
            await event.reply(MENU_TEXTS[lang]["remove_admin_id"])
            USER_STATES[user_id] = "awaiting_remove_admin_id"
        elif USER_STATES.get(user_id) == "awaiting_remove_admin_id":
            try:
                remove_id = int(text)
                add_admin(remove_id, None)
                await event.reply(MENU_TEXTS[lang]["admin_removed"].format(user_id=remove_id))
                await event.reply(get_submenu_text(MENU_TEXTS[lang]["admins_menu"], lang))
                log_action(user_id, f"Removed admin {remove_id}")
                USER_STATES[user_id] = "admins_menu"
            except ValueError:
                await event.reply(MENU_TEXTS[lang]["error_numeric_id"])
                await event.reply(get_submenu_text(MENU_TEXTS[lang]["admins_menu"], lang))
        elif text == MENU_TEXTS[lang]["admins_menu"][3] and level in [1, 2]:
            admins = get_all_admins()
            admin_list = "\n".join([f"{uid} - سطح {get_admin_level(uid)}" if lang == "fa" else f"{uid} - Level {get_admin_level(uid)}" for uid in admins if level == 1 or get_admin_level(uid) > 2])
            await event.reply(MENU_TEXTS[lang]["promote_demote"].format(list=admin_list))
            USER_STATES[user_id] = "awaiting_promote_demote"
        elif USER_STATES.get(user_id) == "awaiting_promote_demote":
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
                USER_STATES[user_id] = "admins_menu"
            except (ValueError, IndexError):
                await event.reply(MENU_TEXTS[lang]["error_invalid_format"])
                await event.reply(get_submenu_text(MENU_TEXTS[lang]["admins_menu"], lang))
        elif text == MENU_TEXTS[lang]["admins_menu"][4]:
            await event.reply(MENU_TEXTS[lang]["welcome"])
            await event.reply(get_main_menu_text(level, lang))
            USER_STATES[user_id] = "main_menu"

    # مدیریت کانال‌ها
    elif text == MENU_TEXTS[lang]["main_menu"][1]:
        channels_menu = MENU_TEXTS[lang]["channels_menu"]
        if level != 1:
            channels_menu = [item for item in channels_menu if item != MENU_TEXTS[lang]["channels_menu"][3]]
        await event.reply(MENU_TEXTS[lang]["channels_menu"][0].split()[0] + ":")
        await event.reply(get_submenu_text(channels_menu, lang))
        USER_STATES[user_id] = "channels_menu"
    elif USER_STATES.get(user_id) == "channels_menu":
        if text == MENU_TEXTS[lang]["channels_menu"][0]:
            channels = get_user_channels(user_id)
            await event.reply(MENU_TEXTS[lang]["channels_list"].format(list="\n".join(channels) if channels else "خالی" if lang == "fa" else "Empty"))
            await event.reply(get_submenu_text(MENU_TEXTS[lang]["channels_menu"], lang))
        elif text == MENU_TEXTS[lang]["channels_menu"][1]:
            await event.reply(MENU_TEXTS[lang]["add_channel_prompt"])
            USER_STATES[user_id] = "awaiting_channel_id"
        elif USER_STATES.get(user_id) == "awaiting_channel_id":
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
                    USER_STATES[user_id] = "awaiting_invite_link"
                else:
                    await event.reply(MENU_TEXTS[lang]["error_invalid_channel"])
                    await event.reply(get_submenu_text(MENU_TEXTS[lang]["channels_menu"], lang))
            USER_STATES[user_id] = "channels_menu"
        elif text == MENU_TEXTS[lang]["channels_menu"][2]:
            await event.reply(MENU_TEXTS[lang]["remove_channel_prompt"])
            USER_STATES[user_id] = "awaiting_remove_channel"
        elif USER_STATES.get(user_id) == "awaiting_remove_channel":
            remove_channel(user_id, text)
            await event.reply(MENU_TEXTS[lang]["channel_removed"])
            await event.reply(get_submenu_text(MENU_TEXTS[lang]["channels_menu"], lang))
            log_action(user_id, f"Removed channel {text}")
            USER_STATES[user_id] = "channels_menu"
        elif text == MENU_TEXTS[lang]["channels_menu"][3] and level == 1:
            await event.reply(MENU_TEXTS[lang]["blacklist_prompt"])
            USER_STATES[user_id] = "awaiting_blacklist"
        elif USER_STATES.get(user_id) == "awaiting_blacklist":
            add_blacklist(text)
            await event.reply(MENU_TEXTS[lang]["blacklist_added"])
            await event.reply(get_submenu_text(MENU_TEXTS[lang]["channels_menu"], lang))
            log_action(user_id, f"Blacklisted channel {text}")
            USER_STATES[user_id] = "channels_menu"
        elif text == MENU_TEXTS[lang]["channels_menu"][4]:
            channels = get_user_channels(user_id)
            await event.reply(MENU_TEXTS[lang]["select_channel"].format(list="\n".join(channels)))
            USER_STATES[user_id] = "awaiting_filter_channel"
        elif USER_STATES.get(user_id) == "awaiting_filter_channel":
            if text in get_user_channels(user_id):
                update_settings(user_id, pending_channel=text)
                await event.reply(MENU_TEXTS[lang]["filter_menu"][0].split()[0] + ":")
                await event.reply(get_submenu_text(MENU_TEXTS[lang]["filter_menu"], lang))
                USER_STATES[user_id] = "filter_menu"
            else:
                await event.reply(MENU_TEXTS[lang]["error_invalid_channel"])
                await event.reply(get_submenu_text(MENU_TEXTS[lang]["channels_menu"], lang))
        elif USER_STATES.get(user_id) == "filter_menu":
            if text == MENU_TEXTS[lang]["filter_menu"][0]:
                await event.reply(MENU_TEXTS[lang]["blacklist_words"])
                USER_STATES[user_id] = "awaiting_blacklist_words"
            elif text == MENU_TEXTS[lang]["filter_menu"][1]:
                await event.reply(MENU_TEXTS[lang]["whitelist_words"])
                USER_STATES[user_id] = "awaiting_whitelist_words"
            elif USER_STATES.get(user_id) == "awaiting_blacklist_words":
                add_filter(user_id, settings["pending_channel"], blacklist=text, whitelist=get_filters(user_id, settings["pending_channel"])["whitelist"])
                await event.reply(MENU_TEXTS[lang]["filter_added"].format(channel=settings["pending_channel"]))
                await event.reply(get_submenu_text(MENU_TEXTS[lang]["filter_menu"], lang))
                log_action(user_id, f"Set blacklist for {settings['pending_channel']}: {text}")
                USER_STATES[user_id] = "filter_menu"
            elif USER_STATES.get(user_id) == "awaiting_whitelist_words":
                add_filter(user_id, settings["pending_channel"], blacklist=get_filters(user_id, settings["pending_channel"])["blacklist"], whitelist=text)
                await event.reply(MENU_TEXTS[lang]["filter_added"].format(channel=settings["pending_channel"]))
                await event.reply(get_submenu_text(MENU_TEXTS[lang]["filter_menu"], lang))
                log_action(user_id, f"Set whitelist for {settings['pending_channel']}: {text}")
                USER_STATES[user_id] = "filter_menu"
            elif text == MENU_TEXTS[lang]["filter_menu"][2]:
                await event.reply(MENU_TEXTS[lang]["channels_menu"][0].split()[0] + ":")
                await event.reply(get_submenu_text(MENU_TEXTS[lang]["channels_menu"], lang))
                USER_STATES[user_id] = "channels_menu"
        elif text == MENU_TEXTS[lang]["channels_menu"][5]:
            await event.reply(MENU_TEXTS[lang]["invite_link_prompt"])
            USER_STATES[user_id] = "awaiting_invite_link"
        elif USER_STATES.get(user_id) == "awaiting_invite_link":
            if text.lower() in ["رد", "skip", "تخطي", "пропустить"]:
                await event.reply(MENU_TEXTS[lang]["channel_skipped"])
                await event.reply(get_submenu_text(MENU_TEXTS[lang]["channels_menu"], lang))
                USER_STATES[user_id] = "channels_menu"
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
                USER_STATES[user_id] = "channels_menu"
        elif text == MENU_TEXTS[lang]["channels_menu"][6]:
            await event.reply(MENU_TEXTS[lang]["channel_skipped"])
            await event.reply(get_submenu_text(MENU_TEXTS[lang]["channels_menu"], lang))
            USER_STATES[user_id] = "channels_menu"
        elif text == MENU_TEXTS[lang]["channels_menu"][7]:
            await event.reply(MENU_TEXTS[lang]["welcome"])
            await event.reply(get_main_menu_text(level, lang))
            USER_STATES[user_id] = "main_menu"

    # ترجمه متن
    elif text == MENU_TEXTS[lang]["main_menu"][2]:
        await event.reply(MENU_TEXTS[lang]["translate_prompt"])
        USER_STATES[user_id] = "awaiting_text_to_translate"
    elif USER_STATES.get(user_id) == "awaiting_text_to_translate":
        translated = translator.translate(text, dest=settings["dest_lang"]).text
        await event.reply(f"ترجمه: {translated}" if lang == "fa" else f"Translation: {translated}")
        await event.reply(get_main_menu_text(level, lang))
        log_action(user_id, f"Translated text: {text}")
        USER_STATES[user_id] = "main_menu"

    # توقف بات
    elif text == MENU_TEXTS[lang]["main_menu"][3] and level == 1:
        await event.reply("شخصی یا گلوبال؟" if lang == "fa" else "Personal or Global?")
        await event.reply(get_submenu_text(MENU_TEXTS[lang]["stop_options"], lang))
        USER_STATES[user_id] = "stop_menu"
    elif USER_STATES.get(user_id) == "stop_menu":
        if text in [f"{MENU_TEXTS[lang]['main_menu'][3]} (شخصی)", f"{MENU_TEXTS[lang]['main_menu'][3]} (Personal)"] or text == MENU_TEXTS[lang]["stop_options"][0]:
            update_settings(user_id, stopped=True)
            await event.reply(MENU_TEXTS[lang]["stop_personal"])
            await event.reply(get_main_menu_text(level, lang))
            log_action(user_id, "Bot stopped personally")
            USER_STATES[user_id] = "main_menu"
        elif text == MENU_TEXTS[lang]["stop_options"][1] and level == 1:
            await event.reply(MENU_TEXTS[lang]["stop_global"])
            log_action(user_id, "Bot stopped globally")
            raise SystemExit
        elif text == MENU_TEXTS[lang]["stop_options"][2]:
            await event.reply(MENU_TEXTS[lang]["welcome"])
            await event.reply(get_main_menu_text(level, lang))
            USER_STATES[user_id] = "main_menu"

    # تنظیمات
    elif text == MENU_TEXTS[lang]["main_menu"][4]:
        await event.reply(MENU_TEXTS[lang]["settings_menu"][0].split()[0] + ":")
        await event.reply(get_submenu_text(MENU_TEXTS[lang]["settings_menu"], lang))
        USER_STATES[user_id] = "settings_menu"
    elif USER_STATES.get(user_id) == "settings_menu":
        if text == MENU_TEXTS[lang]["settings_menu"][0]:
            await event.reply(MENU_TEXTS[lang]["interface_lang"])
            USER_STATES[user_id] = "awaiting_interface_lang"
        elif USER_STATES.get(user_id) == "awaiting_interface_lang":
            if text in ["fa", "en", "ar", "ru"]:
                update_settings(user_id, interface_lang=text)
                await event.reply(f"زبان اینترفیس به {text} تغییر کرد!" if lang == "fa" else f"Interface language changed to {text}!")
                await event.reply(get_submenu_text(MENU_TEXTS[lang]["settings_menu"], lang))
                log_action(user_id, f"Interface language changed to {text}")
            else:
                await event.reply(MENU_TEXTS[lang]["error_invalid_lang"])
                await event.reply(get_submenu_text(MENU_TEXTS[lang]["settings_menu"], lang))
            USER_STATES[user_id] = "settings_menu"
        elif text == MENU_TEXTS[lang]["settings_menu"][1]:
            await event.reply(MENU_TEXTS[lang]["dest_lang"])
            USER_STATES[user_id] = "awaiting_dest_lang"
        elif USER_STATES.get(user_id) == "awaiting_dest_lang":
            update_settings(user_id, dest_lang=text)
            await event.reply(f"زبان مقصد به {text} تغییر کرد!" if lang == "fa" else f"Target language changed to {text}!")
            await event.reply(get_submenu_text(MENU_TEXTS[lang]["settings_menu"], lang))
            log_action(user_id, f"Destination language changed to {text}")
            USER_STATES[user_id] = "settings_menu"
        elif text == MENU_TEXTS[lang]["settings_menu"][2]:
            await event.reply(MENU_TEXTS[lang]["chat_destination"])
            USER_STATES[user_id] = "awaiting_new_chat_destination"
        elif USER_STATES.get(user_id) == "awaiting_new_chat_destination":
            update_settings(user_id, chat_destination=text)
            await event.reply(f"چت مقصد به {text} تغییر کرد!" if lang == "fa" else f"Chat destination changed to {text}!")
            await event.reply(get_submenu_text(MENU_TEXTS[lang]["settings_menu"], lang))
            log_action(user_id, f"Chat destination changed to {text}")
            USER_STATES[user_id] = "settings_menu"
        elif text == MENU_TEXTS[lang]["settings_menu"][3]:
            await event.reply(MENU_TEXTS[lang]["message_format"])
            USER_STATES[user_id] = "awaiting_message_format"
        elif USER_STATES.get(user_id) == "awaiting_message_format":
            if text in ["1", "2"]:
                format_map = {"1": "text_only", "2": "text_with_source"}
                update_settings(user_id, message_format=format_map[text])
                await event.reply(MENU_TEXTS[lang]["format_set"].format(format="فقط متن" if text == "1" and lang == "fa" else "متن + کانال مبدا" if text == "2" and lang == "fa" else "Text only" if text == "1" and lang == "en" else "Text + source channel" if text == "2" and lang == "en"))
                await event.reply(get_submenu_text(MENU_TEXTS[lang]["settings_menu"], lang))
                log_action(user_id, f"Message format set to {format_map[text]}")
            else:
                await event.reply(MENU_TEXTS[lang]["error_invalid_format_choice"])
                await event.reply(get_submenu_text(MENU_TEXTS[lang]["settings_menu"], lang))
            USER_STATES[user_id] = "settings_menu"
        elif text == MENU_TEXTS[lang]["settings_menu"][4]:
            await event.reply(MENU_TEXTS[lang]["welcome"])
            await event.reply(get_main_menu_text(level, lang))
            USER_STATES[user_id] = "main_menu"
