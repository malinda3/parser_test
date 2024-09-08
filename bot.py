import re
import requests
import json
from fake_useragent import UserAgent
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from dotenv import load_dotenv
from typing import Tuple, Optional
import os
from bs4 import BeautifulSoup

# Загрузка переменных из .env файла
load_dotenv()

class ProductParser:
    def __init__(self):
        self.ua = UserAgent()
        print("ProductParser initialized.")

    def get_json_from_html(self, html: str) -> list:
        print("Extracting JSON from HTML.")
        json_data = []
        json_matches = re.findall(r'({.*?})', html)
        for match in json_matches:
            try:
                json_data.append(json.loads(match))
            except json.JSONDecodeError:
                print(f"JSON Decode Error for: {match}")
                continue
        print(f"Found JSON data: {json_data}")
        return json_data

    def parse_json(self, json_data: list) -> Optional[Tuple[str, str]]:
        print("Parsing JSON data.")
        for item in json_data:
            if isinstance(item, dict):
                price = item.get('price', None)
                name = item.get('name', None)
                if price and name:
                    print(f"Parsed JSON data - Name: {name}, Price: {price}")
                    return price, name
            elif isinstance(item, list):
                for sub_item in item:
                    if isinstance(sub_item, dict):
                        result = self.parse_json([sub_item])
                        if result:
                            return result
        print("No valid data found in JSON.")
        return None

    def parse_html(self, html: str) -> Optional[Tuple[str, str]]:
        print("Parsing HTML data.")
        soup = BeautifulSoup(html, 'html.parser')
        
        # Common patterns for finding product names and prices
        name_selectors = [
            ('span', {'class': 'product-name'}),
            ('h1', {'class': 'product-title'}),
            ('h2', {'class': 'product-title'}),
            ('div', {'class': 'product-name'}),
            ('div', {'class': 'product-title'}),
            ('meta', {'property': 'og:title'}),
        ]
        
        price_selectors = [
            ('span', {'class': 'product-price'}),
            ('span', {'class': 'price'}),
            ('div', {'class': 'price'}),
            ('div', {'class': 'product-price'}),
            ('meta', {'property': 'product:price:amount'}),
            ('meta', {'property': 'og:price:amount'}),
        ]
        
        # Extract product name
        name = None
        for tag, attrs in name_selectors:
            name_tag = soup.find(tag, attrs)
            if name_tag:
                name = name_tag.get_text(strip=True)
                if name:
                    break

        # Extract product price
        price = None
        for tag, attrs in price_selectors:
            price_tag = soup.find(tag, attrs)
            if price_tag:
                price = price_tag.get_text(strip=True)
                if price:
                    break

        if name and price:
            print(f"Parsed HTML data - Name: {name}, Price: {price}")
            return price, name
        
        print("No valid data found in HTML.")
        return None


    def collect_info(self, url: str) -> Optional[Tuple[str, str]]:
        print(f"Collecting info from URL: {url}")
        headers = {'User-Agent': self.ua.random}
        response = requests.get(url, headers=headers)
        json_responses = self.get_json_from_html(response.text)
        result = self.parse_json(json_responses)
        if not result:
            result = self.parse_html(response.text)
        if result:
            print(f"Collected info - Name: {result[1]}, Price: {result[0]}")
        else:
            print("No data collected.")
        return result

class ProductParserBot:
    def __init__(self, token):
        print("Initializing bot.")
        self.token = token
        self.commission_rate = float(os.getenv('COMMISSION_RATE', 0.10))  # Комиссия 10%
        self.additional_fee = float(os.getenv('ADDITIONAL_FEE', 50))  # Дополнительная наценка в $50
        self.state = {}  # Словарь для хранения состояния пользователя
        self.parser = ProductParser()  # Инстанцируем парсер
        print(f"Bot initialized with token: {self.token}")

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = update.message.chat_id
        self.state[chat_id] = 'WAITING_FOR_LINK'
        print(f"User {chat_id} started the bot.")
        await update.message.reply_text("send me a link to an item.")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = update.message.chat_id
        text = update.message.text
        print(f"Received message from {chat_id}: {text}")

        if self.state.get(chat_id) == 'WAITING_FOR_LINK':
            if self.is_valid_url(text):
                print(f"Valid URL received: {text}")
                await update.message.reply_text("Looking on your link...")
                product_info = self.parser.collect_info(text)
                if product_info:
                    price, name = product_info
                    try:
                        # Проверяем тип цены и преобразуем в float
                        if isinstance(price, str):
                            price_float = float(price.replace(',', '').replace('$', '').strip())
                        elif isinstance(price, (int, float)):
                            price_float = float(price)
                        else:
                            raise ValueError("Price is not a valid number.")
                    except ValueError:
                        price_float = 0.0
                    price_with_commission = self.calculate_price(price_float)
                    response = (f"Name: {name}\n"
                                f"Our price: {price_with_commission} USD")
                    print(f"Sending response: {response}")
                    await update.message.reply_text(response)
                else:
                    print("Price not found. Asking for currency.")
                    # Если парсинг не удался, предлагаем выбрать валюту
                    self.state[chat_id] = 'WAITING_FOR_CURRENCY'
                    currency_keyboard = [
                        [InlineKeyboardButton("USD", callback_data='USD')],
                        [InlineKeyboardButton("EUR", callback_data='EUR')],
                        [InlineKeyboardButton("GBP", callback_data='GBP')],
                        [InlineKeyboardButton("JPY", callback_data='JPY')]
                    ]
                    reply_markup = InlineKeyboardMarkup(currency_keyboard)
                    await update.message.reply_text("Cant get price.. Please, select a currency, then enter a price from your link.", reply_markup=reply_markup)
            else:
                print("Invalid URL received.")
                await update.message.reply_text("Please, specify a correct link.")
        elif self.state.get(chat_id) == 'WAITING_FOR_PRICE':
            try:
                price = float(text)
                currency = context.user_data.get('currency', 'USD')
                price_with_commission = self.calculate_price(price)
                response = (f"Our price: {price_with_commission} {currency}")
                print(f"Sending response: {response}")
                await update.message.reply_text(response)
                self.state[chat_id] = 'WAITING_FOR_LINK'  # Сбрасываем состояние
            except ValueError:
                print("Invalid price input.")
                await update.message.reply_text("Please, specify a correct price.")

    async def handle_currency_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        chat_id = query.message.chat_id
        currency = query.data
        context.user_data['currency'] = currency  # Сохраняем выбранную валюту
        print(f"User {chat_id} selected currency: {currency}")
        self.state[chat_id] = 'WAITING_FOR_PRICE'  # Переключаем состояние
        await query.message.reply_text(f"You choose {currency}. please, enter price in this currency.")

    def is_valid_url(self, url):
        pattern = re.compile(r'^(?:http|ftp)s?://'  # http:// или https://
                             r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # домен
                             r'localhost|'  # локалхост
                             r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # IP-адрес
                             r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # IPv6-адрес
                             r'(?::\d+)?'  # необязательный порт
                             r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return re.match(pattern, url) is not None

    def calculate_price(self, price):
        price_with_commission = price * (1 + self.commission_rate)
        final_price = price_with_commission + self.additional_fee
        print(f"Calculated price: {final_price}")
        return round(final_price, 2)  # Округляем до двух знаков после запятой

if __name__ == '__main__':
    token = os.getenv('TOKEN')
    bot = ProductParserBot(token)

    app = ApplicationBuilder().token(token).build()

    start_handler = CommandHandler('start', bot.start)
    message_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message)
    currency_handler = CallbackQueryHandler(bot.handle_currency_selection)

    app.add_handler(start_handler)
    app.add_handler(message_handler)
    app.add_handler(currency_handler)

    print("Bot started...")
    app.run_polling()
