import os
import logging
from logging.handlers import RotatingFileHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from dotenv import load_dotenv
import re
import json
import uuid
from datetime import datetime

current_date = datetime.now().strftime('%Y-%m-%d')
log_directory = f'logs/{current_date}'
order_log_directory = f'{log_directory}/orders'
if not os.path.exists(log_directory):
    os.makedirs(log_directory)
if not os.path.exists(order_log_directory):
    os.makedirs(order_log_directory)

log_file = f'{log_directory}/bot.log'
order_log_file = f'{order_log_directory}/orders.log'
log_format = '%(asctime)s - %(levelname)s - %(message)s'

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

file_handler = RotatingFileHandler(log_file, maxBytes=10**6, backupCount=5)
file_handler.setFormatter(logging.Formatter(log_format))
file_handler.setLevel(logging.WARNING)
logger.addHandler(file_handler)

order_logger = logging.getLogger('orders')
order_logger.setLevel(logging.INFO)
order_file_handler = RotatingFileHandler(order_log_file, maxBytes=10**6, backupCount=5)
order_file_handler.setFormatter(logging.Formatter(log_format))
order_logger.addHandler(order_file_handler)

load_dotenv()

class BotHandler:
    def __init__(self, token, commission_rate=float(os.getenv('COMMISSION_RATE')), additional_fee=float(os.getenv('ADDITIONAL_FEE')), min_commission=1000):
        self.token = token
        self.application = Application.builder().token(self.token).build()
        self.commission_rate = commission_rate
        self.additional_fee = additional_fee
        self.min_commission = min_commission
        self.user_data = {}
        self.currencies = {
            'USD': float(os.getenv('usd')),
            'EUR': float(os.getenv('eur')),
            'GBP': float(os.getenv('gbp')),
            'JPY': float(os.getenv('jpy')),
            'CNY': float(os.getenv('cny'))
        }
        self.kafka_topic = "parsing_requests"
        self.kafka_result_topic = "parsing_results"
        self.kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.message.from_user
        logger.info(f"User {user.id} started the bot.")

        keyboard = [
            [InlineKeyboardButton("Оформить заказ", callback_data='order')],
            [InlineKeyboardButton("FAQ", url="https://rusale.shop/individual")],
            [InlineKeyboardButton("Cписок проверенных сайтов", url="https://rusale.shop/trustworthy")],
            [InlineKeyboardButton("Поддержка", url="https://t.me/rusalemngr")],
            [InlineKeyboardButton("Наш канал", url="https://t.me/russsale")],
            [InlineKeyboardButton("Отзывы", url="https://t.me/russsale/1309")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('Выберите опцию:', reply_markup=reply_markup)

    async def handle_menu_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()

        try:
            if query.data == 'order':
                keyboard = [
                    [InlineKeyboardButton("Ввести ссылку", callback_data='input_link')],
                    [InlineKeyboardButton("Ввести цену", callback_data='input_price')],
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.message.edit_text('Выберите вариант ввода:', reply_markup=reply_markup)

            elif query.data == 'input_link':
                await query.message.reply_text('Пожалуйста, отправьте ссылку на товар.')

            elif query.data == 'input_price':
                self.user_data[query.from_user.id] = {'name': 'Manual'}
                await query.message.reply_text('Введите цену с сайта. \nДалее вам будет предложено выбрать валюту, для подсчета примерной стоимости:')
        except Exception as e:
            logger.error(f"Error handling menu selection: {e}")
            if query.message:
                await query.message.reply_text(f'Произошла ошибка. Пожалуйста, попробуйте снова.')

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_message = update.message.text
        user = update.message.from_user
        username = user.username or user.id
        logger.info(f"Received message from {username}: {user_message}")

        try:
            if self.is_valid_url(user_message):
                logger.info(f"Valid URL received: {user_message}")
                request_id = await self.send_to_kafka(user.id, username, user_message)
                await update.message.reply_text(f"Заказ сформирован. Для создания и уточнения деталей передайте ID менеджеру: @rusalemngr\n Ваш ID: {request_id}")
            else:
                await update.message.reply_text('Пожалуйста, отправьте корректную ссылку.')
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            if update.message:
                await update.message.reply_text(f'Произошла ошибка. Пожалуйста, попробуйте снова.')

    async def send_to_kafka(self, user_id, username, url):
        producer = AIOKafkaProducer(bootstrap_servers=self.kafka_bootstrap_servers)
        consumer = AIOKafkaConsumer(
            self.kafka_result_topic,
            bootstrap_servers=self.kafka_bootstrap_servers,
            group_id="bot_group"
        )
        await producer.start()
        await consumer.start()

        try:
            request_id = str(uuid.uuid4())
            
            message = {
                "request_id": request_id,
                "user_id": user_id,
                "username": username,
                "url": url
            }
            
            await producer.send_and_wait(self.kafka_topic, json.dumps(message).encode("utf-8"))
            logger.info(f"Message sent to Kafka: {message}")
            
            async for msg in consumer:
                response = json.loads(msg.value.decode('utf-8'))
                if response.get("request_id") == request_id:
                    product_info = response.get("product_info", {})
                    product_name = product_info.get("name", "Неизвестный продукт")
                    product_price = product_info.get("price", "Неизвестная цена")
                    
                    await self.application.bot.send_message(
                        user_id,
                        f"Название продукта: {product_name}\nЦена: {product_price}"
                    )
                    logger.info(f"Sent product info to user: {product_name} - {product_price}")
                    return request_id
        finally:
            await producer.stop()
            await consumer.stop()

    def is_valid_url(self, url: str) -> bool:
        return url.startswith("http://") or url.startswith("https://")

    def run(self):
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CallbackQueryHandler(self.handle_menu_selection))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        self.application.run_polling()

if __name__ == "__main__":
    load_dotenv()
    bot_token = os.getenv('TOKEN')
    handler = BotHandler(bot_token)
    handler.run()
