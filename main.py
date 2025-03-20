# main.py
from aiogram import Bot, Dispatcher, executor
from config import BOT_TOKEN
from database import init_db
from handlers import register_handlers, monitor_channels, backup_task
import asyncio

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

async def keep_alive():
    while True:
        await asyncio.sleep(300)  # هر ۵ دقیقه یه بار برای پایداری

async def on_startup(_):
    init_db()  # دیتابیس رو راه‌اندازی می‌کنه
    asyncio.create_task(monitor_channels(bot))
    asyncio.create_task(backup_task(bot))
    asyncio.create_task(keep_alive())

if __name__ == "__main__":
    register_handlers(dp)
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
