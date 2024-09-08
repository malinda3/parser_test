from fake_useragent import UserAgent
import requests
import json
import re
from typing import Tuple, Optional

class ProductParser:
    def __init__(self):
        self.ua = UserAgent()

    def get_json_from_html(self, html: str) -> list:
        """Ищем и возвращаем JSON-данные, встроенные в HTML."""
        json_data = []
        json_matches = re.findall(r'({.*?})', html)
        for match in json_matches:
            try:
                json_data.append(json.loads(match))
            except json.JSONDecodeError:
                continue
        return json_data

    def parse_json(self, json_data: list) -> Optional[Tuple[str, str]]:
        """Ищем цену и название товара в JSON-данных."""
        for item in json_data:
            if isinstance(item, dict):
                price = item.get('price', None)
                name = item.get('name', None)
                if price and name:
                    return price, name
            elif isinstance(item, list):
                for sub_item in item:
                    if isinstance(sub_item, dict):
                        result = self.parse_json([sub_item])
                        if result:
                            return result
        return None

    def parse_html(self, html: str) -> Optional[Tuple[str, str]]:
        """Ищем цену и название товара в HTML-коде."""
        price_match = re.search(r'"price":"(\d+\.\d+)"', html)
        name_match = re.search(r'"name":"(.*?)"', html)
        if price_match and name_match:
            return price_match.group(1), name_match.group(1)
        return None

    def collect_info(self, url: str) -> Optional[Tuple[str, str]]:
        """Основная функция сбора информации."""
        headers = {'User-Agent': self.ua.random}
        response = requests.get(url, headers=headers)
        json_responses = self.get_json_from_html(response.text)
        result = self.parse_json(json_responses)
        if not result:
            result = self.parse_html(response.text)
        return result
