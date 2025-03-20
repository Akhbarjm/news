# database.py
import sqlite3
from datetime import datetime, timedelta

def init_db():
    conn = sqlite3.connect("bot_database.db")
    c = conn.cursor()
    # جدول ادمین‌ها
    c.execute('''CREATE TABLE IF NOT EXISTS admins (
        user_id INTEGER PRIMARY KEY, 
        level TEXT,  -- admin, super_admin, master_admin
        language TEXT DEFAULT 'fa', 
        polling_interval INTEGER DEFAULT 60,  -- فاصله پایش به ثانیه
        active INTEGER DEFAULT 1  -- 1 = فعال، 0 = غیرفعال
    )''')
    # جدول کانال‌ها
    c.execute('''CREATE TABLE IF NOT EXISTS channels (
        channel_id TEXT, 
        admin_id INTEGER, 
        white_list TEXT, 
        black_list TEXT,
        FOREIGN KEY(admin_id) REFERENCES admins(user_id)
    )''')
    # جدول مقصدها
    c.execute('''CREATE TABLE IF NOT EXISTS destinations (
        admin_id INTEGER, 
        chat_id TEXT,
        FOREIGN KEY(admin_id) REFERENCES admins(user_id)
    )''')
    # جدول بلک‌لیست مستر ادمین
    c.execute('''CREATE TABLE IF NOT EXISTS blacklist (
        channel_id TEXT PRIMARY KEY
    )''')
    # جدول لاگ‌ها
    c.execute('''CREATE TABLE IF NOT EXISTS logs (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        admin_id INTEGER,
        action TEXT,
        timestamp TEXT
    )''')
    # جدول آخرین آپدیت کانال‌ها
    c.execute('''CREATE TABLE IF NOT EXISTS updates (
        channel_id TEXT PRIMARY KEY,
        last_update_id INTEGER DEFAULT 0
    )''')
    conn.commit()
    conn.close()

def add_admin(user_id, level):
    conn = sqlite3.connect("bot_database.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO admins (user_id, level) VALUES (?, ?)", (user_id, level))
    conn.commit()
    conn.close()

def get_admin(user_id):
    conn = sqlite3.connect("bot_database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM admins WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result

def get_all_admins():
    conn = sqlite3.connect("bot_database.db")
    c = conn.cursor()
    c.execute("SELECT user_id, level FROM admins")
    result = c.fetchall()
    conn.close()
    return result

def add_channel(admin_id, channel_id, white_list="", black_list=""):
    conn = sqlite3.connect("bot_database.db")
    c = conn.cursor()
    c.execute("INSERT INTO channels (channel_id, admin_id, white_list, black_list) VALUES (?, ?, ?, ?)", 
              (channel_id, admin_id, white_list, black_list))
    conn.commit()
    conn.close()

def get_channels(admin_id):
    conn = sqlite3.connect("bot_database.db")
    c = conn.cursor()
    c.execute("SELECT channel_id, white_list, black_list FROM channels WHERE admin_id = ?", (admin_id,))
    result = c.fetchall()
    conn.close()
    return result

def add_destination(admin_id, chat_id):
    conn = sqlite3.connect("bot_database.db")
    c = conn.cursor()
    c.execute("INSERT INTO destinations (admin_id, chat_id) VALUES (?, ?)", (admin_id, chat_id))
    conn.commit()
    conn.close()

def get_destinations(admin_id):
    conn = sqlite3.connect("bot_database.db")
    c = conn.cursor()
    c.execute("SELECT chat_id FROM destinations WHERE admin_id = ?", (admin_id,))
    result = c.fetchall()
    conn.close()
    return [row[0] for row in result]

def add_to_blacklist(channel_id):
    conn = sqlite3.connect("bot_database.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO blacklist (channel_id) VALUES (?)", (channel_id,))
    conn.commit()
    conn.close()

def is_blacklisted(channel_id):
    conn = sqlite3.connect("bot_database.db")
    c = conn.cursor()
    c.execute("SELECT channel_id FROM blacklist WHERE channel_id = ?", (channel_id,))
    result = c.fetchone()
    conn.close()
    return result is not None

def log_action(admin_id, action):
    conn = sqlite3.connect("bot_database.db")
    c = conn.cursor()
    c.execute("INSERT INTO logs (admin_id, action, timestamp) VALUES (?, ?, ?)", 
              (admin_id, action, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_logs():
    conn = sqlite3.connect("bot_database.db")
    c = conn.cursor()
    c.execute("SELECT admin_id, action, timestamp FROM logs")
    result = c.fetchall()
    conn.close()
    return result

def set_active(admin_id, active):
    conn = sqlite3.connect("bot_database.db")
    c = conn.cursor()
    c.execute("UPDATE admins SET active = ? WHERE user_id = ?", (active, admin_id))
    conn.commit()
    conn.close()

def set_language(admin_id, language):
    conn = sqlite3.connect("bot_database.db")
    c = conn.cursor()
    c.execute("UPDATE admins SET language = ? WHERE user_id = ?", (language, admin_id))
    conn.commit()
    conn.close()

def set_polling_interval(admin_id, interval):
    conn = sqlite3.connect("bot_database.db")
    c = conn.cursor()
    c.execute("UPDATE admins SET polling_interval = ? WHERE user_id = ?", (interval, admin_id))
    conn.commit()
    conn.close()

def get_last_update(channel_id):
    conn = sqlite3.connect("bot_database.db")
    c = conn.cursor()
    c.execute("SELECT last_update_id FROM updates WHERE channel_id = ?", (channel_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

def update_last_update(channel_id, update_id):
    conn = sqlite3.connect("bot_database.db")
    c = conn.cursor()1
    c.execute("INSERT OR REPLACE INTO updates (channel_id, last_update_id) VALUES (?, ?)", 
              (channel_id, update_id))
    conn.commit()
    conn.close()

def get_backup():
    conn = sqlite3.connect("bot_database.db")
    with open("backup.db", "wb") as f:
        for line in conn.iterdump():
            f.write(f"{line}\n".encode("utf-8"))
    conn.close()
    return "backup.db"
