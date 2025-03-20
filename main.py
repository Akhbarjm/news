# main.py
from aiogram import Bot, Dispatcher, executor
from config import BOT_TOKEN
from database import init_db
from handlers import register_handlers, monitor_channels, backup_task
import asyncio
from aiohttp import web

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

async def keep_alive():
    while True:
        await asyncio.sleep(300)  # هر ۵ دقیقه یه بار برای جلوگیری از خوابیدن

async def health_check(request):
    return web.Response(text="I'm alive!")  # یه پاسخ ساده برای Render

async def on_startup(_):
    init_db()  # دیتابیس رو راه‌اندازی می‌کنه
    asyncio.create_task(monitor_channels(bot))
    asyncio.create_task(backup_task(bot))
    asyncio.create_task(keep_alive())  # برای Render اضافه شده

app = web.Application()
app.add_routes([web.get('/', health_check)])  # یه مسیر ساده برای پورت

if __name__ == "__main__":
    register_handlers(dp)
    # Polling و وب‌سرور رو با هم اجرا می‌کنه
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
    web.run_app(app, host='0.0.0.0', port=8080)  # پورت 8080 برای Render
