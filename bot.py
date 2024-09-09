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
import asyncio

load_dotenv()

class ProductParser:
    def __init__(self):
        self.ua = UserAgent()

    def get_json_from_html(self, html: str) -> list:
        soup = BeautifulSoup(html, 'html.parser')
        json_data = []
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                json_obj = json.loads(script.string)
                json_data.append(json_obj)
            except json.JSONDecodeError:
                continue
        
        if not json_data:
            json_matches = re.findall(r'({.*?})', html)
            for match in json_matches:
                try:
                    json_data.append(json.loads(match))
                except json.JSONDecodeError:
                    continue
        return json_data

    def parse_json(self, json_data: list) -> Optional[Tuple[str, str]]:
        def extract_info(data):
            if isinstance(data, dict):
                if 'price' in data:
                    price = data['price']
                elif 'offers' in data and 'price' in data['offers']:
                    price = data['offers']['price']
                else:
                    price = None
                
                if 'name' in data:
                    name = data['name']
                elif 'title' in data:
                    name = data['title']
                else:
                    name = None
                
                if price and name:
                    return price, name
            elif isinstance(data, list):
                for item in data:
                    result = extract_info(item)
                    if result:
                        return result
            return None

        for data in json_data:
            result = extract_info(data)
            if result:
                return result

        return None

    def parse_html(self, html: str) -> Optional[Tuple[str, str]]:
        soup = BeautifulSoup(html, 'html.parser')
        
        name = None
        price = None
        
        name_selectors = [
            ('span', {'class': re.compile(r'product.*name', re.I)}),
            ('h1', {'class': re.compile(r'product.*title', re.I)}),
            ('meta', {'property': 'og:title'}),
            ('meta', {'name': 'title'}),
        ]
        
        for tag, attrs in name_selectors:
            name_tag = soup.find(tag, attrs)
            if name_tag:
                name = name_tag.get('content') if tag == 'meta' else name_tag.get_text(strip=True)
                break
        
        price_selectors = [
            ('span', {'class': re.compile(r'product.*price', re.I)}),
            ('span', {'class': re.compile(r'price', re.I)}),
            ('meta', {'property': re.compile(r'price', re.I)}),
            ('div', {'class': re.compile(r'price', re.I)}),
        ]
        
        for tag, attrs in price_selectors:
            price_tag = soup.find(tag, attrs)
            if price_tag:
                price = price_tag.get('content') if tag == 'meta' else price_tag.get_text(strip=True)
                break

        if price:
            price = re.sub(r'[^\d.,]', '', price).replace(',', '')
            try:
                price = float(price)
            except ValueError:
                price = None
        
        if name and price:
            return price, name
        return None

    async def collect_info(self, url: str) -> Optional[Tuple[str, str]]:
        headers = {'User-Agent': self.ua.random}
        response = requests.get(url, headers=headers)
        
        try:
            json_responses = self.get_json_from_html(response.text)
            result = self.parse_json(json_responses)
            if not result:
                result = self.parse_html(response.text)
            return result
        except asyncio.TimeoutError:
            return None

class ProductParserBot:
    def __init__(self, token):
        print("Initializing bot.")
        self.token = token
        self.commission_rate = os.getenv('COMMISSION_RATE')
        self.additional_fee = os.getenv('ADDITIONAL_FEE')
        self.state = {} 
        self.parser = ProductParser()
        print(f"Bot initialized with token: {self.token}")

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = update.message.chat_id
        self.state[chat_id] = 'WAITING_FOR_LINK'
        print(f"User {chat_id} started the bot.")
        await update.message.reply_text("Send me a link to an item.")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = update.message.chat_id
        text = update.message.text
        print(f"Received message from {chat_id}: {text}")

        if self.state.get(chat_id) == 'WAITING_FOR_LINK':
            if self.is_valid_url(text):
                print(f"Valid URL received: {text}")
                await update.message.reply_text("Looking at your link...")
                try:
                    product_info = await asyncio.wait_for(self.parser.collect_info(text), timeout=15.0)
                except asyncio.TimeoutError:
                    product_info = None

                if product_info:
                    price, name = product_info
                    try:
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
                self.state[chat_id] = 'WAITING_FOR_LINK'
            except ValueError:
                print("Invalid price input.")
                await update.message.reply_text("Please, specify a correct price.")

    async def handle_currency_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        chat_id = query.message.chat_id
        currency = query.data
        context.user_data['currency'] = currency
        print(f"User {chat_id} selected currency: {currency}")
        self.state[chat_id] = 'WAITING_FOR_PRICE'
        await query.message.reply_text(f"You choose {currency}. please, enter price in this currency.")

    def is_valid_url(self, url):
        pattern = re.compile(r'^(?:http|ftp)s?://' 
                             r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
                             r'localhost|'
                             r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|' 
                             r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'
                             r'(?::\d+)?'
                             r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return re.match(pattern, url) is not None

    def calculate_price(self, price: float) -> float:
        return round(price * (1 + self.commission_rate) + self.additional_fee, 2)

if __name__ == '__main__':
    bot_token = os.getenv('TOKEN')
    bot = ProductParserBot(bot_token)
    
    application = ApplicationBuilder().token(bot_token).build()

    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    application.add_handler(CallbackQueryHandler(bot.handle_currency_selection))

    print("Bot started...")
    application.run_polling()
