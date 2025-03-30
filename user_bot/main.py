import os
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
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

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Отправьте ссылку на товар.")

def is_url(text: str) -> bool:
    return text.startswith("http://") or text.startswith("https://")

async def handle_message(update: Update, context: CallbackContext):
    text = update.message.text

    logger.info(f"Received message from {update.message.from_user.id}: {text}")

    if not is_url(text):
        return

    if not API_URL:
        await update.message.reply_text("API_URL не задан. Запросы к API пропущены.")
        return

    user_id = update.message.from_user.id
    username = update.message.from_user.username or "Неизвестно"
    first_name = update.message.from_user.first_name or "Неизвестно"
    last_name = update.message.from_user.last_name or "Неизвестно"

    request_data = {
    "url": text,
    "request_id": str(get_next_request_id()),
    "user_id": username,
    }

    logger.info(f"Sending request to {API_URL} with data: {request_data}")

    try:
        response = requests.post(API_URL, json=request_data)

        logger.info(f"Request sent to {API_URL} with response status: {response.status_code}")
        logger.info(f"Response content: {response.text}")

        if response.status_code != 200:
            await update.message.reply_text(f"Ошибка API. Статус: {response.status_code}")
            logger.error(f"API returned status: {response.status_code}")
            return

        data = response.json()
        
        if "ProductInfo" not in data:
            await update.message.reply_text("Не удалось получить информацию о товаре.")
            return

        product_info = data["product_info"]
        name = product_info.get("Name", "Неизвестно")
        price = product_info.get("Price", "Неизвестно")

        await update.message.reply_text(f"Название: {name}\nЦена: {price}")

    except requests.RequestException as e:
        logger.error(f"Ошибка при запросе к API: {e}")
        await update.message.reply_text("Произошла ошибка при запросе к API.")


def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()

if __name__ == '__main__':
    main()
