import sqlite3
import logging

logging.basicConfig(filename="bot.log", level=logging.INFO, format="%(asctime)s - %(message)s")

def init_db():
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS admins (user_id INTEGER PRIMARY KEY, level INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS channels (user_id INTEGER, channel_id TEXT, added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (user_id, channel_id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS blacklist (channel_id TEXT PRIMARY KEY)''')
    c.execute('''CREATE TABLE IF NOT EXISTS settings (user_id INTEGER PRIMARY KEY, interface_lang TEXT DEFAULT 'fa', dest_lang TEXT DEFAULT 'en', chat_destination TEXT, stopped INTEGER DEFAULT 0, pending_level INTEGER, pending_channel TEXT, message_format TEXT DEFAULT 'text_with_source', invite_link TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS filters (user_id INTEGER, channel_id TEXT, blacklist TEXT, whitelist TEXT, PRIMARY KEY (user_id, channel_id))''')
    conn.commit()
    conn.close()

def add_admin(user_id, level):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    if level is None:
        c.execute("DELETE FROM admins WHERE user_id = ?", (user_id,))
    else:
        c.execute("INSERT OR REPLACE INTO admins (user_id, level) VALUES (?, ?)", (user_id, level))
    c.execute("INSERT OR IGNORE INTO settings (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def get_admin_level(user_id):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("SELECT level FROM admins WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def get_all_admins():
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("SELECT user_id FROM admins")
    result = c.fetchall()
    conn.close()
    return [row[0] for row in result]

def add_channel(user_id, channel_id):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO channels (user_id, channel_id) VALUES (?, ?)", (user_id, channel_id))
    conn.commit()
    conn.close()

def get_user_channels(user_id):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("SELECT channel_id FROM channels WHERE user_id = ? ORDER BY added_at", (user_id,))
    result = c.fetchall()
    conn.close()
    return [row[0] for row in result]

def remove_channel(user_id, channel_id):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("DELETE FROM channels WHERE user_id = ? AND channel_id = ?", (user_id, channel_id))
    c.execute("DELETE FROM filters WHERE user_id = ? AND channel_id = ?", (user_id, channel_id))
    conn.commit()
    conn.close()

def adjust_channels_on_demote(user_id, new_level):
    limits = {1: 20, 2: 20, 3: 15, 4: 10}
    channels = get_user_channels(user_id)
    if len(channels) > limits[new_level]:
        excess = len(channels) - limits[new_level]
        for channel in channels[-excess:]:
            remove_channel(user_id, channel)
        return excess
    return 0

def add_blacklist(channel_id):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO blacklist (channel_id) VALUES (?)", (channel_id,))
    conn.commit()
    conn.close()

def is_blacklisted(channel_id):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("SELECT channel_id FROM blacklist WHERE channel_id = ?", (channel_id,))
    result = c.fetchone()
    conn.close()
    return bool(result)

def get_user_settings(user_id):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("SELECT interface_lang, dest_lang, chat_destination, stopped, pending_level, pending_channel, message_format, invite_link FROM settings WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return {"interface_lang": result[0], "dest_lang": result[1], "chat_destination": result[2], "stopped": result[3], "pending_level": result[4], "pending_channel": result[5], "message_format": result[6], "invite_link": result[7]} if result else {"interface_lang": "fa", "dest_lang": "en", "chat_destination": None, "stopped": 0, "pending_level": None, "pending_channel": None, "message_format": "text_with_source", "invite_link": None}

def update_settings(user_id, **kwargs):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO settings (user_id) VALUES (?)", (user_id,))
    for key, value in kwargs.items():
        c.execute(f"UPDATE settings SET {key} = ? WHERE user_id = ?", (value, user_id))
    conn.commit()
    conn.close()

def add_filter(user_id, channel_id, blacklist=None, whitelist=None):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO filters (user_id, channel_id, blacklist, whitelist) VALUES (?, ?, ?, ?)", (user_id, channel_id, blacklist, whitelist))
    conn.commit()
    conn.close()

def get_filters(user_id, channel_id):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("SELECT blacklist, whitelist FROM filters WHERE user_id = ? AND channel_id = ?", (user_id, channel_id))
    result = c.fetchone()
    conn.close()
    return {"blacklist": result[0], "whitelist": result[1]} if result else {"blacklist": None, "whitelist": None}

def log_action(user_id, action):
    logging.info(f"User {user_id}: {action}")