## Краткая информация, саммари

Бот для парсинга цен из интернет магазинов

Парсер и бот работают отдельно, сейчас надо убрать гпт код из бота, добавить весь функционал, заявленный заказчиком

В последнем изменении добавил около 500 строк юнит тестов для бота. 17 фейл 51 пасс.

## Как запустить бота:
создать .env:
```
TOKEN='token from @BotFather'
COMMISSION_RATE=0.10
ADDITIONAL_FEE=50
```
команда для запуска бота:
```
python main_bot.py
```

для запуска тестов парсера надо раскоментить мейн вместе с методом теста, после чего

```
python ProductParser.py
```
для запуска юнит-тестов
```
python -m pytest UnitTest.py
```

## как пользоваться ботом:

Написать /start

отправить ссылку на товар
## todo:
Бот дружит с парсером, задуматься над созданием заказов

улучшение парсера

## пояснения по файлам

ProductParser.py - актуальный парсер, работает со многими сайтами, есть метод test, так же добавлены юнит тесты отдельными файликами.

bot.py - попытка подружить бота и парсер, почти успешно, надо дорабатывать функционал, так же в нем много гпт кода, я бы хотел переписать его сам.

UnitTest.py - юнит тесты, будут активно дописываться чатом гпт.

main.py - тестовый вариант парсера, который должен выгружать данные с магазинов. Пока работа работает только с https://shop.palaceskateboards.com