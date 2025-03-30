import os
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_URL = os.getenv("API_URL")

if not BOT_TOKEN:
    logger.error("BOT_TOKEN is not set in the environment variables")
    exit(1)

if not API_URL:
    logger.warning("API_URL is not set. API requests will be skipped.")


async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Отправьте ссылку на товар.")


def is_url(text: str) -> bool:
    return text.startswith("http://") or text.startswith("https://")


async def handle_message(update: Update, context: CallbackContext):
    text = update.message.text

    if not is_url(text):
        return

    if not API_URL:
        await update.message.reply_text("API_URL не задан. Запросы к API пропущены.")
        return

    try:
        response = requests.post(API_URL, json={"url": text})

        if response.status_code != 200:
            await update.message.reply_text(f"Ошибка API. Статус: {response.status_code}")
            logger.error(f"API returned status: {response.status_code}")
            return

        data = response.json()

        if "ProductInfo" not in data:
            await update.message.reply_text("Не удалось получить информацию о товаре.")
            return

        product_info = data["ProductInfo"]
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
