import os
import logging
import requests
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    ConversationHandler
)
from telegram.error import InvalidToken

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_URL = os.getenv("API_URL")

if not BOT_TOKEN:
    logger.error("BOT_TOKEN is not set in the environment variables")
    exit(1)

if not API_URL:
    logger.warning("API_URL is not set. API requests will be skipped.")

logger.info(f"Bot token set: {BOT_TOKEN[:4]}...{BOT_TOKEN[-4:]}")

current_request_id = 0
ORDER_STATE = 1  # State for ordering flow

def get_next_request_id():
    global current_request_id
    current_request_id += 1
    return current_request_id

def check_bot_token(token: str):
    try:
        bot = requests.get(f"https://api.telegram.org/bot{token}/getMe")
        if bot.status_code == 200:
            result = bot.json()
            if not result["ok"]:
                raise InvalidToken("Invalid token provided by Telegram API.")
            logger.info(f"Bot connected successfully: {result['result']['username']}")
        else:
            raise InvalidToken(f"Failed to verify token, status code: {bot.status_code}")
    except Exception as e:
        logger.error(f"Error validating bot token: {e}")
        exit(1)

check_bot_token(BOT_TOKEN)

def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton("🛍 Оформить заказ")],
            [KeyboardButton("📖 FAQ"), KeyboardButton("🛡 Проверенные сайты")],
            [KeyboardButton("👤 Поддержка"), KeyboardButton("📢 Канал"), KeyboardButton("💬 Отзывы")]
        ],
        resize_keyboard=True
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Выберите действие:",
        reply_markup=get_main_menu()
    )

def is_url(text: str) -> bool:
    return text.startswith("http://") or text.startswith("https://")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    logger.info(f"Received message from {update.message.from_user.id}: {text}")

    if text == "🛍 Оформить заказ":
        await update.message.reply_text(
            "Отправьте ссылку на товар.",
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton("🔙 В меню")]], resize_keyboard=True)
        )
        return ORDER_STATE

    elif text == "📖 FAQ":
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Открыть FAQ", url="https://rusale.shop/individual")]])
        await update.message.reply_text("📖 Часто задаваемые вопросы:", reply_markup=keyboard)

    elif text == "🛡 Проверенные сайты":
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Открыть список сайтов", url="https://rusale.shop/trustworthy")]])
        await update.message.reply_text("🛡 Проверенные сайты:", reply_markup=keyboard)

    elif text == "👤 Поддержка":
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Написать в поддержку", url="https://t.me/rusalemngr")]])
        await update.message.reply_text("👤 Свяжитесь с нашей поддержкой:", reply_markup=keyboard)

    elif text == "📢 Канал":
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Перейти в канал", url="https://t.me/russsale")]])
        await update.message.reply_text("📢 Наш Telegram-канал:", reply_markup=keyboard)

    elif text == "💬 Отзывы":
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Читать отзывы", url="https://t.me/russsale/1309")]])
        await update.message.reply_text("💬 Отзывы наших клиентов:", reply_markup=keyboard)

    else:
        await update.message.reply_text("Пожалуйста, выберите действие из меню.")

    return ConversationHandler.END

async def handle_order_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text == "🔙 В меню":
        await update.message.reply_text("Вы вернулись в главное меню.", reply_markup=get_main_menu())
        return ConversationHandler.END

    if not is_url(text):
        await update.message.reply_text("Пожалуйста, отправьте корректную ссылку или нажмите 🔙 В меню.")
        return ORDER_STATE

    if not API_URL:
        await update.message.reply_text("API_URL не задан. Запросы к API пропущены.")
        return ConversationHandler.END

    user = update.message.from_user
    request_data = {
        "url": text,
        "request_id": str(get_next_request_id()),
        "user_id": user.username or "Неизвестно",
        "id": user.id
    }

    logger.info(f"Sending request to {API_URL} with data: {request_data}")

    try:
        response = requests.post(API_URL, json=request_data)
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response content: {response.text}")

        if response.status_code != 200:
            await update.message.reply_text(f"Ошибка API. Статус: {response.status_code}")
            return ORDER_STATE

        data = response.json()
        product_info = data.get("product_info", {})
        name = product_info.get("name", "Неизвестно")
        price = product_info.get("price", "Неизвестно")

        # Добавляем "руб." к числу, если это число
        if isinstance(price, (int, float)):
            price = f"{price} руб."

        await update.message.reply_text(f"Название: {name}\nЦена: {price}")
        await update.message.reply_text("Вы вернулись в главное меню.", reply_markup=get_main_menu())
        return ConversationHandler.END

    except requests.RequestException as e:
        logger.error(f"Ошибка при запросе к API: {e}")
        await update.message.reply_text("Произошла ошибка при запросе к API.")
        return ORDER_STATE

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start), MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)],
        states={
            ORDER_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_order_link)]
        },
        fallbacks=[],
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    main()
