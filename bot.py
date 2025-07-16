import asyncio
import logging
from aiogram import Bot, Dispatcher
from handlers import setup_handlers
from database import init_db

# Конфигурация
API_TOKEN = 'YOUR TOKEN'
LOG_LEVEL = logging.INFO

# Настройка логирования
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Инициализация и запуск бота."""
    logger.info("Starting bot...")
    
    # Инициализация базы данных
    init_db()
    
    # Инициализация бота
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher()
    
    # Настройка обработчиков
    setup_handlers(dp)
    
    # Запуск бота
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
    finally:
        await bot.session.close()

if __name__ == '__main__':
    asyncio.run(main())