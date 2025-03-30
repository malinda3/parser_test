import os
import logging
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Устанавливаем уровень логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Получаем значения из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_URL = os.getenv("API_URL")

# Проверяем, что переменные окружения заданы
if not BOT_TOKEN:
    logger.error("BOT_TOKEN is not set in the environment variables")
    exit(1)

if not API_URL:
    logger.warning("API_URL is not set. API requests will be skipped.")


# Функция для обработки команды /start
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Отправьте ссылку на товар.")


# Функция для проверки, является ли сообщение ссылкой
def is_url(text: str) -> bool:
    return text.startswith("http://") or text.startswith("https://")


# Функция для обработки текста с ссылкой на товар
def handle_message(update: Update, context: CallbackContext):
    text = update.message.text

    # Если сообщение не является ссылкой, игнорируем
    if not is_url(text):
        return

    if not API_URL:
        update.message.reply_text("API_URL не задан. Запросы к API пропущены.")
        return

    try:
        # Отправка запроса на внешний API
        response = requests.post(API_URL, json={"url": text})

        if response.status_code != 200:
            update.message.reply_text(f"Ошибка API. Статус: {response.status_code}")
            logger.error(f"API returned status: {response.status_code}")
            return

        # Парсим ответ от API
        data = response.json()

        if "ProductInfo" not in data:
            update.message.reply_text("Не удалось получить информацию о товаре.")
            return

        product_info = data["ProductInfo"]
        name = product_info.get("Name", "Неизвестно")
        price = product_info.get("Price", "Неизвестно")

        # Отправляем информацию о товаре пользователю
        update.message.reply_text(f"Название: {name}\nЦена: {price}")

    except requests.RequestException as e:
        logger.error(f"Ошибка при запросе к API: {e}")
        update.message.reply_text("Произошла ошибка при запросе к API.")


def main():
    # Создаем объект Updater с токеном бота
    updater = Updater(token=BOT_TOKEN)

    # Получаем диспетчер для обработки команд и сообщений
    dispatcher = updater.dispatcher

    # Добавляем обработчики для команд и сообщений
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # Запуск бота
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
