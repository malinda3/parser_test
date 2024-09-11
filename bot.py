from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import logging
from ProductParser import ProductParser 
import os
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
load_dotenv()

class BotHandler:
    def __init__(self, token, commission_rate=float(os.getenv('COMMISSION_RATE')), additional_fee=float(os.getenv('ADDITIONAL_FEE'))):
        self.token = token
        self.application = Application.builder().token(self.token).build()
        self.commission_rate = commission_rate
        self.additional_fee = additional_fee
        self.user_data = {}

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.message.from_user
        logging.info(f"User {user.id} started the bot.")

        # Создаем кнопки меню
        keyboard = [
            [InlineKeyboardButton("Оформить заказ", callback_data='order')],
            [InlineKeyboardButton("Мои заказы", callback_data='my_orders')],
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

        if query.data == 'order':
            await query.message.reply_text('Пожалуйста, отправьте ссылку на продукт.')
            return
        
        elif query.data == 'my_orders':
            # Здесь можно добавить обработку для просмотра заказов
            await query.message.reply_text('Здесь будут ваши заказы.')

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_message = update.message.text
        user = update.message.from_user
        logging.info(f"Received message from {user.id}: {user_message}")

        if self.is_valid_url(user_message):
            logging.info(f"Valid URL received: {user_message}")
            product_info = self.get_product_info(user_message)

            if product_info['price'] != "Price not found":
                response = f"Product Name: {product_info['name']}\nProduct Price: {product_info['price']}"
                await update.message.reply_text(response)
            else:
                self.user_data[user.id] = {'name': product_info['name'], 'url': user_message}
                await update.message.reply_text('Could not find the price. Please enter the price manually:')
        else:
            if user.id in self.user_data and self.is_number(user_message):
                manual_price = float(user_message)
                final_price = manual_price * (1 + self.commission_rate) + self.additional_fee
                await update.message.reply_text(
                    f"Manual Price: {manual_price}\n"
                    f"Final Price: {final_price:.2f}"
                )
                del self.user_data[user.id]
            else:
                await update.message.reply_text('Please send a valid product link or a valid number.')

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

        logging.info("Bot starting...")
        self.application.run_polling()

if __name__ == "__main__":
    bot_token = os.getenv('TOKEN')
    bot = BotHandler(bot_token)
    bot.run()
