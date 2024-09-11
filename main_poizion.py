import requests
import json
import re

# Base URL for the Poizon Express website
base_url = 'https://poizon.poizonexpress.ru/page/'

# Initialize an empty list to store products
all_products = []

# Iterate through the pages (assuming there are 317 pages)
for page_num in range(1, 318):
    url = f'{base_url}{page_num}/'
    response = requests.get(url).text
    
    # Adjust this pattern according to the site's structure
    pattern = re.compile(r'\{.*?\}', re.DOTALL)

    matches = pattern.findall(response)

    if matches:
        for match in matches:
            try:
                # Attempt to load each JSON block
                product = json.loads(match)
                all_products.append(product)
            except json.JSONDecodeError as e:
                print(f"Ошибка при декодировании JSON на странице {page_num}: {e}")
    else:
        print(f"Не удалось найти данные на странице {page_num}.")

# Save the collected products to a JSON file
with open('poizon_products.json', 'w') as f:
    json.dump(all_products, f, indent=4)

print("Данные успешно сохранены в 'poizon_products.json'.")
