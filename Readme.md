## Как запустить бота:
.env:
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
## todo:
подружить обновленный парсер из ProductParser.py с ботом, убрать из бота гпт код, оптимизировать парсер для остальных сайтв.

## пояснения по файлам

bot.py - изначальный с файл с ботом и старым парсером, скоро потрется изза неактаульности

ProductParser.py - актуальный парсер, работает со многими сайтами, есть метод test.

main_bot.py - попытка подружить бота и парсер, почти успешно, но что то со значениями.