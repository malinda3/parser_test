from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
    ConversationHandler,
    CallbackQueryHandler
)
import logging
import os
import asyncpg
from typing import Dict, Any

# Настройка логгирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация БД
DB_CONFIG = {
    "user": "admin",
    "password": "test123",
    "database": "parserdb",
    "host": "postgres",
    "port": "5432"
}

# Состояния ConversationHandler
GET_TEXT, GET_PHOTO_URL, CONFIRM_SEND = range(3)
ALLOWED_USER_IDS = {5876847299, 1845807637}  # Ваши ID админов

def get_confirm_keyboard(with_photo: bool) -> InlineKeyboardMarkup:
    buttons = []
    if with_photo:
        buttons.append([InlineKeyboardButton("✅ Отправить с фото", callback_data='send_with_photo')])
    buttons.append([InlineKeyboardButton("📤 Отправить без фото", callback_data='send_without_photo')])
    buttons.append([InlineKeyboardButton("❌ Отменить", callback_data='cancel')])
    return InlineKeyboardMarkup(buttons)

async def retranslate_start(update: Update, context: CallbackContext) -> int:
    """Начало процесса ретрансляции"""
    if update.effective_user.id not in ALLOWED_USER_IDS:
        await update.message.reply_text("⛔ У вас нет прав для этой команды")
        return ConversationHandler.END
    
    context.user_data.clear()
    await update.message.reply_text(
        "📝 Введите текст сообщения для рассылки:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Отменить", callback_data='cancel')]])
    )
    return GET_TEXT

async def handle_text(update: Update, context: CallbackContext) -> int:
    """Обработка текста сообщения"""
    context.user_data['message_text'] = update.message.text
    await update.message.reply_text(
        "🖼 Прикрепите URL изображения (или нажмите /skip чтобы пропустить):",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Пропустить", callback_data='skip_photo')]])
    )
    return GET_PHOTO_URL

async def handle_photo_url(update: Update, context: CallbackContext) -> int:
    """Обработка URL фото"""
    if update.message.text.startswith(('http://', 'https://')):
        context.user_data['photo_url'] = update.message.text
        preview_msg = f"📝 Текст:\n---------------------------------------\n {context.user_data['message_text']}\n\n---------------------------------------\n🖼 Фото: {update.message.text}"
    else:
        await update.message.reply_text("❌ Некорректный URL. Используйте http:// или https://")
        return GET_PHOTO_URL
    
    await update.message.reply_text(
        f"🔍 Предпросмотр:\n{preview_msg}",
        reply_markup=get_confirm_keyboard(with_photo='photo_url' in context.user_data)
    )
    return CONFIRM_SEND

async def skip_photo(update: Update, context: CallbackContext) -> int:
    """Пропуск прикрепления фото"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        f"📝 Текст сообщения:\n{context.user_data['message_text']}\n\n"
        "Фото не прикреплено",
        reply_markup=get_confirm_keyboard(with_photo=False)
    )
    return CONFIRM_SEND

async def confirm_send(update: Update, context: CallbackContext) -> int:
    """Подтверждение и рассылка"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'cancel':
        await query.edit_message_text("❌ Рассылка отменена")
        return ConversationHandler.END
    
    try:
        connection = await asyncpg.connect(**DB_CONFIG)
        users = await connection.fetch("SELECT DISTINCT user_id FROM parsed_data")
        
        if not users:
            await query.edit_message_text("❌ Нет пользователей для рассылки")
            return ConversationHandler.END
        
        success = failed = 0
        message = context.user_data['message_text']
        photo_url = context.user_data.get('photo_url')
        
        await query.edit_message_text(f"🔄 Рассылка для {len(users)} пользователей...")
        
        for user in users:
            try:
                chat_id = int(user['user_id'])
                if query.data == 'send_with_photo' and photo_url:
                    await context.bot.send_photo(
                        chat_id=chat_id,
                        photo=photo_url,
                        caption=message
                    )
                else:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=message
                    )
                success += 1
            except Exception as e:
                logger.error(f"Ошибка отправки {user['user_id']}: {e}")
                failed += 1
        
        await query.edit_message_text(
            f"✅ Готово!\nУспешно: {success}\nНе удалось: {failed}"
        )
    except Exception as e:
        logger.error(f"Ошибка рассылки: {e}")
        await query.edit_message_text(f"❌ Ошибка: {str(e)}")
    finally:
        if 'connection' in locals():
            await connection.close()
    
    return ConversationHandler.END

# Настройка обработчиков
def setup_handlers(application: Application) -> None:
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('retranslate', retranslate_start)],
        states={
            GET_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)],
            GET_PHOTO_URL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_photo_url),
                CallbackQueryHandler(skip_photo, pattern='^skip_photo$')
            ],
            CONFIRM_SEND: [
                CallbackQueryHandler(confirm_send, pattern='^(send_with_photo|send_without_photo|cancel)$')
            ]
        },
        fallbacks=[CommandHandler('cancel', lambda u,c: ConversationHandler.END)]
    )
    application.add_handler(conv_handler)

# Запуск бота
if __name__ == '__main__':
    app = Application.builder().token(os.getenv("BOT_TOKEN")).build()
    setup_handlers(app)
    app.run_polling()