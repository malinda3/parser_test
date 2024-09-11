from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import logging
from ProductParser import ProductParser
import os
from dotenv import load_dotenv
import re

logging.basicConfig(level=logging.INFO)
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
        logging.info(f"User {user.id} started the bot.")

        # Создаем кнопки меню
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
                    [InlineKeyboardButton("Назад", callback_data='back_to_menu')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.message.edit_text('Выберите вариант ввода:', reply_markup=reply_markup)

            elif query.data == 'back_to_menu':
                await self.start(update, context)

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
                                    f"Примерная цена: {final_price:.2f} RUB\n"
                                    f"Ссылка на товар: {url}\n"
                                    f"Для оформления заказа перешлите это сообщение: https://t.me/rusalemngr")
                        await query.message.edit_text(response)
                        del self.user_data[user_id]
                    except ValueError as e:
                        logging.error(f"ValueError: {e}")
                        await query.message.reply_text(f'Произошла ошибка: {str(e)}')
                else:
                    await query.message.reply_text('Что-то пошло не так, попробуйте снова.')

            elif query.data == 'input_link':
                await query.message.reply_text('Пожалуйста, отправьте ссылку на товар.')

            elif query.data == 'input_price':
                self.user_data[query.from_user.id] = {'name': 'Manual'}
                await query.message.reply_text('Введите цену с сайта. \nДалее вам будет предложено выбрать валюту, для подсчета примерной стоимости:')

        except Exception as e:
            logging.error(f"Error handling menu selection: {e}")
            if query.message:
                await query.message.reply_text(f'Произошла ошибка: {str(e)}')

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_message = update.message.text
        user = update.message.from_user
        logging.info(f"Received message from {user.id}: {user_message}")

        try:
            if self.is_valid_url(user_message):
                logging.info(f"Valid URL received: {user_message}")
                product_info = self.get_product_info(user_message)

                if product_info['price'] != "Price not found":
                    self.user_data[user.id] = {'name': product_info['name'], 'price': product_info['price'], 'url': user_message}
                    await self.ask_for_currency(update)
                else:
                    self.user_data[user.id] = {'name': product_info['name'], 'url': user_message}
                    await update.message.reply_text('Не получается найти цену автоматически. Пожалуйста, введите цену с сайта. \nДалее вам будет предложено выбрать валюту, для подсчета примерной стоимости:')
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
            logging.error(f"Error handling message: {e}")
            if update.message:
                await update.message.reply_text(f'Произошла ошибка: {str(e)}')

    async def ask_for_currency(self, update: Update) -> None:
        keyboard = [
            [InlineKeyboardButton("USD", callback_data='currency_usd')],
            [InlineKeyboardButton("EUR", callback_data='currency_eur')],
            [InlineKeyboardButton("GBP", callback_data='currency_gbp')],
            [InlineKeyboardButton("JPY", callback_data='currency_jpy')],
            [InlineKeyboardButton("CNY", callback_data='currency_cny')]
        ]
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
        self.application.add_handler(CallbackQueryHandler(self.handle_menu_selection, pattern='^(order|back_to_menu|input_link|input_price|currency_)'))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

        logging.info("Bot starting...")
        self.application.run_polling()

if __name__ == "__main__":
    bot_token = os.getenv('TOKEN')
    bot = BotHandler(bot_token)
    bot.run()
