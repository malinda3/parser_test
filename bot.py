import os
import logging
from logging.handlers import RotatingFileHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from ProductParser import ProductParser
from dotenv import load_dotenv
import re
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

# Общий логгер
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)  # Устанавливаем уровень логирования для всего приложения

# Обработчик для записи в файл
file_handler = RotatingFileHandler(log_file, maxBytes=10**6, backupCount=5)
file_handler.setFormatter(logging.Formatter(log_format))
file_handler.setLevel(logging.WARNING)  # Записываем предупреждения и ошибки в основной лог-файл
logger.addHandler(file_handler)

# Логгер для заказов
order_logger = logging.getLogger('orders')
order_logger.setLevel(logging.INFO)
order_file_handler = RotatingFileHandler(order_log_file, maxBytes=10**6, backupCount=5)
order_file_handler.setFormatter(logging.Formatter(log_format))  # Формат с временной меткой и уровнем INFO
order_logger.addHandler(order_file_handler)

load_dotenv()

class BotHandler:
    def __init__(self, token, commission_rate=float(os.getenv('COMMISSION_RATE')), additional_fee=float(os.getenv('ADDITIONAL_FEE'))):
        self.token = token
        self.application = Application.builder().token(self.token).build()
        self.commission_rate = commission_rate
        self.additional_fee = additional_fee
        self.user_data = {}
        self.currencies = {
            'USD': float(os.getenv('usd')),
            'EUR': float(os.getenv('eur')),
            'GBP': float(os.getenv('gbp')),
            'JPY': float(os.getenv('jpy')),
            'CNY': float(os.getenv('cny'))
        }

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.message.from_user
        logger.info(f"User {user.id} started the bot.")

        keyboard = [
            [InlineKeyboardButton("Оформить заказ", callback_data='order')],
            [InlineKeyboardButton("FAQ", url="https://rusale.shop/individual")],
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

            elif query.data.startswith('currency_'):
                selected_currency = query.data.split('_')[1].upper()
                user_id = query.from_user.id

                if 'price' in self.user_data.get(user_id, {}):
                    try:
                        price = float(re.sub(r'[^\d.]+', '', self.user_data[user_id]['price']))
                        currency_rate = self.currencies[selected_currency]
                        final_price = price * currency_rate * (1 + self.commission_rate) + self.additional_fee

                        url = self.user_data[user_id].get('url', 'Не указана')
                        response = (f"Название: {self.user_data[user_id]['name']}\n"
                                    f"Цена на сайте: {self.user_data[user_id]['price']} {selected_currency}\n"
                                    f"Цена без доставки: {final_price:.0f} RUB\n"
                                    f"Ссылка на товар: {url}\n"
                                    f"Для оформления заказа перешлите это сообщение: https://t.me/rusalemngr")
                        await query.message.edit_text(response)
                        
                        # Логирование информации о формировании заказа
                        order_logger.info(f"Order created by User {user_id}: Name: {self.user_data[user_id]['name']}, "
                                    f"Price: {self.user_data[user_id]['price']} {selected_currency}, "
                                    f"Final Price: {final_price:.0f} RUB")

                        del self.user_data[user_id]
                    except ValueError as e:
                        logger.error(f"ValueError: {e}")
                        await query.message.reply_text(f'Произошла ошибка при обработке цены. Пожалуйста, попробуйте снова.')
                else:
                    await query.message.reply_text('Что-то пошло не так, попробуйте снова.')

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
        logger.info(f"Received message from {user.id}: {user_message}")

        try:
            if self.is_valid_url(user_message):
                logger.info(f"Valid URL received: {user_message}")
                product_info = self.get_product_info(user_message)

                if product_info['price'] != "Price not found":
                    self.user_data[user.id] = {'name': product_info['name'], 'price': product_info['price'], 'url': user_message}
                    await self.ask_for_currency(update)

                    # Логирование информации о создании заказа
                    order_logger.info(f"New order created by User {user.id}: Name: {product_info['name']}, "
                                f"Price: {product_info['price']}, URL: {user_message}")

                else:
                    self.user_data[user.id] = {'name': product_info['name'], 'url': user_message}
                    await update.message.reply_text('Не получается найти цену автоматически.\nПожалуйста, введите цену с сайта. \nДалее вам будет предложено выбрать валюту, для подсчета примерной стоимости:')
            else:
                if user.id in self.user_data:
                    if self.is_number(user_message):
                        self.user_data[user.id]['price'] = user_message
                        await self.ask_for_currency(update)
                    else:
                        await update.message.reply_text('Пожалуйста, введите корректную цену.')
                else:
                    await update.message.reply_text('Пожалуйста, отправьте правильную ссылку на товар или введите сумму с сайта.')
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            if update.message:
                await update.message.reply_text(f'Произошла ошибка. Пожалуйста, попробуйте снова.')

    async def ask_for_currency(self, update: Update) -> None:
        buttons = [InlineKeyboardButton(curr, callback_data=f'currency_{curr.lower()}') for curr in self.currencies.keys()]
        keyboard = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('Выберите валюту:', reply_markup=reply_markup)

    def is_valid_url(self, url: str) -> bool:
        return url.startswith("http://") or url.startswith("https://")

    def is_number(self, text: str) -> bool:
        try:
            float(text)
            return True
        except ValueError:
            return False

    def get_product_info(self, url: str) -> dict:
        parser = ProductParser(url)
        return parser.get_product_info()

    def run(self):
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CallbackQueryHandler(self.handle_menu_selection))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        self.application.run_polling()

if __name__ == '__main__':
    bot_token = os.getenv('TOKEN')
    bot_handler = BotHandler(token=bot_token)
    bot_handler.run()
