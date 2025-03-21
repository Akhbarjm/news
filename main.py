from aiogram import Bot, Dispatcher, executor
from config import BOT_TOKEN
from handlers import register_handlers

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

async def on_startup(_):
    print("Bot started!")  # برای دیباگ

if __name__ == "__main__":
    register_handlers(dp)
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
