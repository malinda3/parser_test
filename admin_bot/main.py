from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from telegram.error import InvalidToken
import logging
import os

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    await update.message.reply_text(f"Привет, {user.first_name}! Я эхо-бот. Просто напиши мне что-нибудь, и я повторю это.")

async def echo(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(update.message.text)

async def error_handler(update: Update, context: CallbackContext) -> None:
    logger.error(f'Ошибка при обработке сообщения: {context.error}')

def main() -> None:
    try:
        BOT_TOKEN = os.getenv("BOT_TOKEN")
        application = Application.builder().token(BOT_TOKEN).build()
        
        application.add_handler(CommandHandler("start", start))
        
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
        
        application.add_error_handler(error_handler)
        
        logger.info("Бот запущен...")
        application.run_polling()
        
    except InvalidToken:
        logger.error("Неверный токен бота! Пожалуйста, проверьте токен.")
    except Exception as e:
        logger.error(f"Ошибка: {e}")

if __name__ == '__main__':
    main()