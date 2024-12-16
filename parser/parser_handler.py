import json
from confluent_kafka import Consumer, KafkaException, Producer
from ProductParser import ProductParser
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Настройки Kafka
KAFKA_BOOTSTRAP_SERVERS = 'kafka:9092'
KAFKA_TOPIC_REQUEST = 'parsing_requests'
KAFKA_TOPIC_RESULT = 'parsing_results'

# Настройка консьюмера Kafka
config = {
    'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
    'group.id': 'my-consumer-group',
    'auto.offset.reset': 'earliest'
}

consumer = Consumer(config)

# Настройка продюсера Kafka для отправки результатов
producer = Producer({'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS})

consumer.subscribe([KAFKA_TOPIC_REQUEST])

logger.info(f"Listening to topic '{KAFKA_TOPIC_REQUEST}'...")

def send_result_to_kafka(result_message):
    """
    Функция отправки обработанного результата обратно в Kafka.
    """
    producer.produce(KAFKA_TOPIC_RESULT, json.dumps(result_message).encode('utf-8'))
    producer.flush()
    logger.info(f"Sent result to Kafka: {result_message}")

def process_message(message):
    """
    Функция обработки сообщения из Kafka.
    1. Извлекаем ссылку.
    2. Парсим информацию о продукте с помощью ProductParser.
    3. Отправляем результат обратно в Kafka.
    """
    try:
        url = message['url']
        logger.info(f"Processing URL: {url}")

        # Получение информации о продукте
        parser = ProductParser(url)
        product_info = parser.get_product_info()
        
        # Подготовка сообщения для отправки в Kafka
        result_message = {
            'request_id': message['request_id'],
            'user_id': message['user_id'],
            'product_info': product_info
        }
        
        # Отправка результата обратно в Kafka
        send_result_to_kafka(result_message)

    except Exception as e:
        logger.error(f"Error processing message: {e}")

# Основной цикл для потребления сообщений
try:
    while True:
        msg = consumer.poll(timeout=1.0)

        if msg is None:
            continue  # Нет сообщения, продолжаем слушать

        if msg.error():
            if msg.error().code() == KafkaException._PARTITION_EOF:
                logger.info(f"End of partition reached {msg.topic()} [{msg.partition()}]")
            else:
                logger.error(f"Error: {msg.error()}")
        else:
            # Декодируем сообщение из Kafka
            message = json.loads(msg.value().decode('utf-8'))
            logger.info(f"Received message: {message}")

            # Обрабатываем полученное сообщение
            process_message(message)

except KeyboardInterrupt:
    logger.info("\nConsumer stopped manually.")

finally:
    consumer.close()
    producer.flush()
    logger.info("Consumer and producer closed.")
