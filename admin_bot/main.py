from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, Bot
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
import sys
import asyncio
import asyncpg
from typing import Dict, Any
import json
from collections import defaultdict
from datetime import datetime

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
# состояния бота при /retranslate
GET_TEXT, GET_PHOTO_URL, CONFIRM_SEND = range(3)
# Загрузка секрета с юзерами
def load_allowed_users() -> set[int]:
    users_str = os.getenv("ALLOWED_USER_IDS", "")
    if not users_str:
        return set()
    return {int(user_id.strip()) for user_id in users_str.split(",")}

ALLOWED_USER_IDS = load_allowed_users()

def get_confirm_keyboard(with_photo: bool) -> InlineKeyboardMarkup:
    buttons = []
    if with_photo:
        buttons.append([InlineKeyboardButton("✅ Отправить с фото", callback_data='send_with_photo')])
    buttons.append([InlineKeyboardButton("📤 Отправить без фото", callback_data='send_without_photo')])
    buttons.append([InlineKeyboardButton("❌ Отменить", callback_data='cancel')])
    return InlineKeyboardMarkup(buttons)

async def retranslate_start(update: Update, context: CallbackContext) -> int:
    """Начало процесса рассылки"""
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
        
        # Создаем временного бота
        sender_bot = Bot(token=os.getenv("USER_BOT_TOKEN"))
        
        try:
            for user in users:
                try:
                    chat_id = int(user['user_id'])
                    if query.data == 'send_with_photo' and photo_url:
                        await sender_bot.send_photo(
                            chat_id=chat_id,
                            photo=photo_url,
                            caption=message
                        )
                    else:
                        await sender_bot.send_message(
                            chat_id=chat_id,
                            text=message
                        )
                    success += 1
                except Exception as e:
                    logger.error(f"Ошибка отправки {user['user_id']}: {e}")
                    failed += 1
        finally:
            await sender_bot.close()
        
        await query.edit_message_text(
            f"✅ Рассылка завершена! Успешно: {success}, Ошибки: {failed}\n"
            "🔄 Приложение перезапускается..."
        )
        
        await asyncio.sleep(2)
        
        application = context.application
        await application.stop()
        execl(sys.executable, sys.executable, *sys.argv)
        
    except Exception as e:
        logger.error(f"Ошибка рассылки: {e}")
        await query.edit_message_text(f"❌ Ошибка: {str(e)}")
    finally:
        if 'connection' in locals():
            await connection.close()
    
    return ConversationHandler.END
# Функция для списка заказов
async def count_handler(update: Update, context: CallbackContext) -> None:
    """Обработчик команды /count — статистика по заказам с товарами, ценами и датами"""
    if update.effective_user.id not in ALLOWED_USER_IDS:
        await update.message.reply_text("⛔ У вас нет прав для этой команды")
        return

    try:
        connection = await asyncpg.connect(**DB_CONFIG)
        rows = await connection.fetch("""
            SELECT user_id, content, created_at
            FROM parsed_data
            ORDER BY user_id, created_at;
        """)
        await connection.close()

        if not rows:
            await update.message.reply_text("🔍 В базе нет данных.")
            return

        # Группировка заказов по user_id
        user_orders = defaultdict(list)

        for row in rows:
            uid = row["user_id"] or "неизвестно"

            try:
                content = json.loads(row["content"])
                name = content.get("name", "Без названия")
                price = content.get("price", "Без цены")
            except Exception as e:
                logger.warning(f"Ошибка парсинга JSON для {uid}: {e}")
                name = "❌ Ошибка"
                price = "—"

            try:
                created_at = row["created_at"].strftime('%Y-%m-%d %H:%M')
            except Exception as e:
                created_at = "—"

            user_orders[uid].append((name, price, created_at))

        def pluralize(count: int) -> str:
            if count % 10 == 1 and count % 100 != 11:
                return "заказ"
            elif 2 <= count % 10 <= 4 and (count % 100 < 10 or count % 100 >= 20):
                return "заказа"
            else:
                return "заказов"

        lines = ["📊 Статистика по пользователям:\n"]
        for uid, orders in user_orders.items():
            count = len(orders)
            word = pluralize(count)
            lines.append(f"👤 {uid} – {count} {word}:")
            for name, price, created in orders:
                lines.append(f"  • {name} — {price}")
            lines.append("")

        await update.message.reply_text("\n".join(lines).strip())

    except Exception as e:
        logger.error(f"Ошибка в /count: {e}")
        await update.message.reply_text("❌ Ошибка при обращении к базе.")

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
    application.add_handler(CommandHandler("count", count_handler))
    application.add_handler(conv_handler)

# Запуск бота
if __name__ == '__main__':
    app = Application.builder().token(os.getenv("BOT_TOKEN")).build()
    setup_handlers(app)
    app.run_polling()