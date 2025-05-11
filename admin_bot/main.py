from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
    ConversationHandler,
    CallbackQueryHandler 
)
from telegram.error import InvalidToken
import logging
import os
import asyncpg
from typing import List, Set
from telegram.ext import ConversationHandler

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
RETRANSLATE_MESSAGE, CONFIRM_SEND = range(2)
ALLOWED_USER_IDS = set(map(int, os.getenv('ALLOWED_USER_IDS', '').split(',')))
START_MESSAGE = """

Доступные команды:
/start - показать это сообщение
/test - проверить подключение к БД и получить список пользователей
/retranslate - спам сообщений 
"""
async def retranslate_start(update: Update, context: CallbackContext) -> int:
    """Начало процесса ретрансляции"""
    if update.effective_user.id not in ALLOWED_USER_IDS:
        await update.message.reply_text("⛔ У вас нет прав для выполнения этой команды")
        return ConversationHandler.END
    
    await update.message.reply_text(
        "📝 Введите сообщение для рассылки:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Отмена", callback_data='cancel')]
        ])
    )
    return RETRANSLATE_MESSAGE

async def retranslate_message(update: Update, context: CallbackContext) -> int:
    """Получение сообщения для рассылки"""
    context.user_data['message_to_send'] = update.message.text
    
    await update.message.reply_text(
        f"✉️ Сообщение для рассылки:\n\n{update.message.text}\n\n"
        f"Отправить это сообщение всем пользователям?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Да", callback_data='confirm')],
            [InlineKeyboardButton("❌ Нет", callback_data='cancel')]
        ])
    )
    return CONFIRM_SEND

async def retranslate_confirm(update: Update, context: CallbackContext) -> int:
    """Подтверждение и отправка сообщения"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'confirm':
        try:
            connection = await asyncpg.connect(**DB_CONFIG)
            user_ids = await connection.fetch("SELECT DISTINCT user_id FROM parsed_data")
            
            if not user_ids:
                await query.edit_message_text("❌ В базе данных нет пользователей для рассылки")
                return ConversationHandler.END
            
            success = 0
            failed = 0
            message = context.user_data['message_to_send']
            await query.edit_message_text(message)
            await query.edit_message_text(f"🔄 Начинаю рассылку для {len(user_ids)} пользователей...")
            
            for user in user_ids:
                try:
                    await context.bot.send_message(
                        chat_id=user['user_id'],
                        text=message
                    )
                    success += 1
                except Exception as e:
                    logger.error(f"Ошибка отправки пользователю {user['user_id']}: {e}")
                    failed += 1
            
            await query.edit_message_text(
                f"✅ Рассылка завершена:\n"
                f"Успешно: {success}\n"
                f"Не удалось: {failed}"
            )
        except Exception as e:
            logger.error(f"Ошибка при работе с БД: {e}")
            await query.edit_message_text("❌ Ошибка при получении списка пользователей")
        finally:
            if 'connection' in locals():
                await connection.close()
    else:
        await query.edit_message_text("❌ Рассылка отменена")
    
    return ConversationHandler.END

async def retranslate_cancel(update: Update, context: CallbackContext) -> int:
    """Отмена рассылки"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("❌ Рассылка отменена")
    return ConversationHandler.END

async def send_start_message(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(START_MESSAGE)

async def echo(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(update.message.text)

async def test_handler(update: Update, context: CallbackContext) -> None:
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
    """Обновленная настройка обработчиков"""
    retranslate_handler = ConversationHandler(
        entry_points=[CommandHandler('retranslate', retranslate_start)],
        states={
            RETRANSLATE_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, retranslate_message)],
            CONFIRM_SEND: [CallbackQueryHandler(retranslate_confirm, pattern='^confirm$'),
                          CallbackQueryHandler(retranslate_cancel, pattern='^cancel$')]
        },
        fallbacks=[CommandHandler('cancel', retranslate_cancel)]
    )
    
    application.add_handler(retranslate_handler)
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