import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import re
import logging

logging.basicConfig(level=logging.INFO)

class ProductParser:
    def __init__(self, url, timeout=15):
        self.url = url
        self.timeout = timeout
        self.ua = UserAgent()
        self.headers = {'User-Agent': self.ua.random}
        self.soup = None
        self.product_name = None
        self.product_price = None

    def fetch_page(self):
        try:
            response = requests.get(self.url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            self.soup = BeautifulSoup(response.text, 'html.parser')
        except requests.exceptions.HTTPError as http_err:
            logging.error(f"HTTP error occurred: {http_err}")
        except requests.exceptions.Timeout:
            logging.error(f"Timeout after {self.timeout} seconds on {self.url}.")
        except Exception as err:
            logging.error(f"Other error occurred: {err}")

    def parse_product_name(self):
        if self.soup:
            search_tags = ['h1', 'h2', 'h3', 'title', 'div', 'span']
            search_classes = ['product-title', 'product-name', 'name', 'title']
            
            for tag in search_tags:
                product_name_tag = self.soup.find(tag)
                if product_name_tag:
                    self.product_name = product_name_tag.get_text(strip=True)
                    return
            
            for cls in search_classes:
                product_name_tag = self.soup.find(class_=cls)
                if product_name_tag:
                    self.product_name = product_name_tag.get_text(strip=True)
                    return

            self.product_name = "Name not found"
            logging.warning("Cannot find product name.")
        else:
            logging.error("No content to parse for product name.")

    def parse_product_price(self):
        if self.soup:
            currency_symbols = r'[£$€¥₹]'
            product_price_tag = self.soup.find('span', string=lambda text: re.search(currency_symbols, text) if text else False)
            
            if product_price_tag:
                price_text = product_price_tag.get_text(strip=True)
                price_text = re.sub(r'[^\d\.,£$€¥₹]', '', price_text)
                price_text = re.sub(r'\s+', '', price_text)

                numeric_price = re.search(rf'({currency_symbols}\d{{1,3}}(,\d{{3}})*(\.\d+)?|\d{{1,3}}(,\d{{3}})*(\.\d+)?\s*{currency_symbols})', price_text)
                if numeric_price:
                    self.product_price = numeric_price.group(0).strip()
                else:
                    self.product_price = "Price not found"
                    logging.warning("Cannot extract price.")
            else:
                self.product_price = "Price not found"
                logging.warning("Cannot find price element.")
        else:
            self.product_price = "Price not found"
            logging.error("No content to parse for product price.")


    def get_product_info(self):
        self.fetch_page()
        self.parse_product_name()
        self.parse_product_price()
        return {
            'name': self.product_name,
            'price': self.product_price
        }
        
    def get_product_name(self):
        self.fetch_page()
        self.parse_product_name()
        return self.product_name

    def get_product_price(self):
        self.fetch_page()
        self.parse_product_price()
        return self.product_price

    @staticmethod
    def test():
        urls = [
            'https://faworldentertainment.com/collections/bottoms/products/salt-and-pepper-canvas-double-knee-pant',
            'https://shop.palaceskateboards.com/products/a7oh8xvpjvqf',
            'https://www.asos.com/asos-design/asos-design-fine-knit-boat-neck-top-in-cream/prd/205945056#colourWayId-205945063',
            'https://www.grailed.com/listings/67108758-arc-teryx-x-streetwear-x-vintage-vintage-hat-arcteryx-cap-outdoor-gore-tex-arcteryx?g_aidx=Listing_by_heat_production&g_aqid=02fab20a807c337cc1a14ed9de6d2154',
            'https://stockx.com/air-jordan-4-retro-white-thunder?size=4',
            'https://www.farfetch.com/nl/shopping/men/palm-angels-hermosa-item-25038217.aspx',
            'https://shop.doverstreetmarket.com/collections/comme-des-garcons-play/products/play-unisex-parka-1-carry-over-ax-t344-051-1',
            'https://www.ebay.com/itm/126523570030?_nkw=fuckingawesome+t+shirt&itmmeta=01J7AT6Q804YB77VR8C1EGQTXX&hash=item1d7564776e:g:S~cAAOSwFUBmZ4b8&itmprp=enc%3AAQAJAAAA8HoV3kP08IDx%2BKZ9MfhVJKnQqNnglOE7vrjZDWo73ZBuvjZPZ6Ek9rmfm9giPGiBO9D2FlDJzpvQ3OL9UWVt4DEUrR73ycQsFsuc9CfidOpLNAQDn5eTkIDJ%2FEwl8EBbBYchgWkFArjF22Dw%2FybvPqVMMgzM1hyGIVfvQSK3HUeVZhlT9zoRO14iy%2BhRKbugMNTTsEcHyGisNoMgGZGvDEah%2FTWL2ks61ObEkfxjWdsEFSdgOQYni4MevdQx8rdg0XQHSCBsmKRH0acnX9N%2Fv4yjHiNXlQcXx39eSes%2BJaahO8ZrZ0pXJcvgM0D5824cAA%3D%3D%7Ctkp%3ABk9SR4r0mtq6ZA',
            'https://www.carhartt-wip.com/en/men-featured-9/og-detroit-jacket-winter-malbec-black-aged-canvas-964_1',
            'https://itkkit.com/catalog/product/246455_thisisneverthat-regular-jeans-red/',
            'https://www.drmartens.com/eu/en_eu/sinclair-milled-nappa-leather-platform-boots-black/p/22564001',
            'https://fuckthepopulation.com/collections/shop/products/made-in-hell-leather-puffer-coatwhite',
            'https://dimemtl.com/collections/dime-fall-24/products/fa24-coverstitch-sherpa-fleece-military-brown',
            'https://kith.com/collections/mens-footwear/products/aaih3432',
            #'https://shop-jp.doverstreetmarket.com/collections/asics/products/asics-ub8-s-gt-2160-400'
        ]
        
        for url in urls:
            parser = ProductParser(url)
            product_info = parser.get_product_info()
            
            logging.info(f"URL: {url}")
            logging.info(f"Name: {product_info['name']}")
            logging.info(f"Price: {product_info['price']}")
            logging.info('-' * 40)

if __name__ == "__main__":
    ProductParser.test()

    #url = "https://faworldentertainment.com/collections/bottoms/products/salt-and-pepper-canvas-double-knee-pant"
    #parser = ProductParser(url)
    #product_info = parser.get_product_info()
    #logging.info(f"Name: {product_info['name']}")
    #logging.info(f"Price: {product_info['price']}")
