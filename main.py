import asyncio
from telethon import TelegramClient, events
from config import API_ID, API_HASH, PHONE
from database import init_db
from handlers import handle_new_message, handle_admin_message

# تنظیمات اولیه Telethon
client = TelegramClient('session_name', API_ID, API_HASH)

# هندل کردن پیام‌های جدید از کانال‌ها
@client.on(events.NewMessage)
async def new_message_handler(event):
    await handle_new_message(event, client)

# هندل کردن پیام‌های ادمین‌ها
@client.on(events.NewMessage)
async def admin_message_handler(event):
    await handle_admin_message(event, client)

# شروع برنامه
async def main():
    init_db()
    await client.start(phone=PHONE)
    print("اتصال برقرار شد!")
    await client.run_until_disconnected()

if __name__ == "__main__":
    client.loop.run_until_complete(main())
