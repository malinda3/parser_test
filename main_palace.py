import requests
import json
import re

link = 'https://shop.palaceskateboards.com/'
response = requests.get(link).text

# Используем более точное регулярное выражение для поиска полных JSON-объектов
pattern = re.compile(r'\{"availableForSale".*?"compareAtPrice":null\}\]\}\}', re.DOTALL)

matches = pattern.findall(response)

if matches:
    items = []

    for match in matches:
        try:
            # Загружаем каждый JSON блок отдельно
            product = json.loads(match)
            items.append(product)
        except json.JSONDecodeError as e:
            print(f"Ошибка при декодировании JSON: {e}")

    # Сохраняем данные в файл JSON
    with open('palace_products.json', 'w') as f:
        json.dump(items, f, indent=4)

    print("Данные успешно сохранены в 'palace_products.json'.")
else:
    print("Не удалось найти данные о товарах на странице.")
