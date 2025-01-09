import json
import asyncio
from aiohttp import ClientSession
from confluent_kafka import Consumer, KafkaException, Producer
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Настройки Kafka
KAFKA_BOOTSTRAP_SERVERS = 'kafka:9092'
KAFKA_TOPIC_REQUEST = 'parsing_requests'
KAFKA_TOPIC_RESULT = 'parsing_results'

# Настройка Kafka Consumer
consumer_config = {
    'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
    'group.id': 'my-consumer-group',
    'auto.offset.reset': 'earliest'
}
consumer = Consumer(consumer_config)

# Настройка Kafka Producer
producer = Producer({'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS})

# Подписываемся на тему
consumer.subscribe([KAFKA_TOPIC_REQUEST])

# Асинхронная отправка результата в Kafka
def send_result_to_kafka(producer, result_message):
    producer.produce(KAFKA_TOPIC_RESULT, json.dumps(result_message).encode('utf-8'))
    producer.poll(0)  # Пуллим продюсера для обработки событий
    logger.info(f"Sent result to Kafka: {result_message}")

# Асинхронный класс ProductParser
class ProductParser:
    def __init__(self, url):
        self.url = url

    async def get_product_info(self):
        async with ClientSession() as session:
            async with session.get(self.url) as response:
                html = await response.text()
                # Здесь должна быть ваша логика парсинга, например, парсинг цены
                # Пример:
                from bs4 import BeautifulSoup  # Используем BeautifulSoup для парсинга HTML
                soup = BeautifulSoup(html, 'html.parser')
                price = soup.find('span', {'class': 'price'}).text if soup.find('span', {'class': 'price'}) else 'Price not found'
                return {"url": self.url, "price": price}

# Асинхронная обработка сообщения
async def process_message(message):
    """
    Обработка одного сообщения:
    1. Извлечение URL.
    2. Парсинг информации о продукте.
    3. Отправка результата в Kafka.
    """
    try:
        url = message['url']
        logger.info(f"Processing URL: {url}")

        # Создание парсера и получение информации о продукте
        parser = ProductParser(url)
        product_info = await parser.get_product_info()

        # Подготовка результата
        result_message = {
            'request_id': message['request_id'],
            'user_id': message['user_id'],
            'product_info': product_info
        }

        # Отправка результата обратно в Kafka
        send_result_to_kafka(producer, result_message)

    except Exception as e:
        logger.error(f"Error processing message: {e}")

# Основной асинхронный цикл потребления сообщений
async def consume_messages():
    logger.info(f"Listening to topic '{KAFKA_TOPIC_REQUEST}'...")
    try:
        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                await asyncio.sleep(0.1)  # Ждём немного, если сообщений нет
                continue

            if msg.error():
                logger.error(f"Kafka error: {msg.error()}")
                continue

            # Расшифровка сообщения
            message = json.loads(msg.value().decode('utf-8'))
            logger.info(f"Received message: {message}")

            # Асинхронно обрабатываем сообщение
            await process_message(message)

    except KeyboardInterrupt:
        logger.info("Consumer stopped manually.")

    finally:
        consumer.close()
        producer.flush()

# Запуск асинхронного цикла
if __name__ == '__main__':
    asyncio.run(consume_messages())
