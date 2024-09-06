from fake_useragent import UserAgent
import requests
import json
import re
import os

ua = UserAgent()

def sanitize_filename(filename):
    invalid_chars = '<>:"/\\|?*'
    return ''.join(char if char not in invalid_chars else '_' for char in filename)

def save_response(url, response_text):
    base_url = url.split('//')[1].replace('/', '_')
    base_url = sanitize_filename(base_url)
    html_file = f"{base_url}.html"
    json_file = f"{base_url}.json"

    json_data = get_json_from_html(response_text)
    
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(response_text)
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=4)

def get_json_from_html(html):
    """Ищем JSON-данные, встроенные в HTML."""
    json_data = []
    
    json_matches = re.findall(r'({.*?})', html)
    
    for match in json_matches:
        try:
            json_data.append(json.loads(match))
        except json.JSONDecodeError:
            continue
    
    return json_data

def collect_info(url):
    """Сохраняем HTML и JSON данные для указанного URL."""
    headers = {'User-Agent': ua.random}
    response = requests.get(url, headers=headers)
    
    print(f"Сохранение данных с {url}")

    save_response(url, response.text)

def main():
    urls = [
        'https://shop.palaceskateboards.com/products/e3rsgaiyoo7s',
        'https://faworldentertainment.com/collections/bottoms/products/salt-and-pepper-canvas-double-knee-pant',
        'https://www.grailed.com/listings/65762769-bape-bape-star-slides?g_aidx=Listing_production&g_aqid=2812009d63f1df02381c8798c3239f27'
    ]
    
    if not os.path.exists('data'):
        os.makedirs('data')
    
    os.chdir('data')
    
    for url in urls:
        collect_info(url)

if __name__ == '__main__':
    main()
