import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import TELEGRAM_BOT_TOKEN
from database import Database
from handlers import setup_routers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    # Initialize bot and dispatcher
    bot = Bot(token=TELEGRAM_BOT_TOKEN, parse_mode=ParseMode.MARKDOWN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Initialize database
    db = Database()
    await db.connect()
    logger.info("Database connected")

    # Setup routers
    main_router = setup_routers()
    dp.include_router(main_router)

    # Inject database into handlers via middleware
    @dp.update.middleware()
    async def db_middleware(handler, event, data):
        data["db"] = db
        return await handler(event, data)

    # Start polling
    logger.info("Starting bot...")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await db.disconnect()
        await bot.session.close()
        logger.info("Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
