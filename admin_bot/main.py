from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from telegram.error import InvalidToken
import logging
import os
import asyncpg
from typing import List

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

DB_CONFIG = {
    "user": "admin",
    "password": "test123",
    "database": "parserdb",
    "host": "postgres",
    "port": "5432"
}

START_MESSAGE = """

Доступные команды:
/start - показать это сообщение
/test - проверить подключение к БД и получить список пользователей
"""

async def send_start_message(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(START_MESSAGE)

async def echo(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(update.message.text)

async def test_handler(update: Update, context: CallbackContext) -> None:
    ALLOWED_USER_IDS = {5876847299, 1845807637}
    
    user_id = update.effective_user.id
    
    if user_id not in ALLOWED_USER_IDS:
        await update.message.reply_text("У вас нет прав для выполнения этой команды")
        return
    try:
        connection = await asyncpg.connect(**DB_CONFIG)
        
        query = "SELECT DISTINCT user_id FROM parsed_data"
        user_ids: List[str] = await connection.fetch(query)
        
        if user_ids:
            response = "Список user_id:\n" + "\n".join([user['user_id'] for user in user_ids])
        else:
            response = "В базе данных нет записей"
        
        await update.message.reply_text(response)
        
    except Exception as e:
        logger.error(f"Ошибка при работе с БД: {e}")
        await update.message.reply_text(f"Ошибка при подключении к БД: {e}")
    finally:
        if 'connection' in locals():
            await connection.close()

async def error_handler(update: Update, context: CallbackContext) -> None:
    """Обработчик ошибок"""
    logger.error(f'Ошибка при обработке сообщения: {context.error}')

def setup_handlers(application: Application) -> None:
    """Настройка обработчиков команд"""
    application.add_handler(CommandHandler("start", send_start_message))
    application.add_handler(CommandHandler("test", test_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    application.add_error_handler(error_handler)

if __name__ == '__main__':
    try:
        BOT_TOKEN = os.getenv("BOT_TOKEN")
        if not BOT_TOKEN:
            raise ValueError("Не указан токен бота в переменной окружения BOT_TOKEN")
            
        application = Application.builder().token(BOT_TOKEN).build()
        setup_handlers(application)
        
        logger.info("Бот запущен...")
        application.run_polling()
        
    except InvalidToken:
        logger.error("Неверный токен бота! Пожалуйста, проверьте токен.")
    except Exception as e:
        logger.error(f"Ошибка: {e}")