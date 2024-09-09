#ok#https://faworldentertainment.com/collections/bottoms/products/salt-and-pepper-canvas-double-knee-pant
#ok#https://shop.palaceskateboards.com/products/a7oh8xvpjvqf
#неправильная цена#https://www.asos.com/asos-design/asos-design-fine-knit-boat-neck-top-in-cream/prd/205945056#colourWayId-205945063
#ok#https://www.grailed.com/listings/67108758-arc-teryx-x-streetwear-x-vintage-vintage-hat-arcteryx-cap-outdoor-gore-tex-arcteryx?g_aidx=Listing_by_heat_production&g_aqid=02fab20a807c337cc1a14ed9de6d2154
#не дает ничего выгрузить#https://stockx.com/air-jordan-4-retro-white-thunder?size=4
#не дает ничего выгрузить#https://www.farfetch.com/nl/shopping/men/palm-angels-hermosa-item-25038217.aspx
#ok#https://shop.doverstreetmarket.com/collections/comme-des-garcons-play/products/play-unisex-parka-1-carry-over-ax-t344-051-1
#не дает ничего выгрузить#https://www.ebay.com/itm/126523570030?_nkw=fuckingawesome+t+shirt&itmmeta=01J7AT6Q804YB77VR8C1EGQTXX&hash=item1d7564776e:g:S~cAAOSwFUBmZ4b8&itmprp=enc%3AAQAJAAAA8HoV3kP08IDx%2BKZ9MfhVJKnQqNnglOE7vrjZDWo73ZBuvjZPZ6Ek9rmfm9giPGiBO9D2FlDJzpvQ3OL9UWVt4DEUrR73ycQsFsuc9CfidOpLNAQDn5eTkIDJ%2FEwl8EBbBYchgWkFArjF22Dw%2FybvPqVMMgzM1hyGIVfvQSK3HUeVZhlT9zoRO14iy%2BhRKbugMNTTsEcHyGisNoMgGZGvDEah%2FTWL2ks61ObEkfxjWdsEFSdgOQYni4MevdQx8rdg0XQHSCBsmKRH0acnX9N%2Fv4yjHiNXlQcXx39eSes%2BJaahO8ZrZ0pXJcvgM0D5824cAA%3D%3D%7Ctkp%3ABk9SR4r0mtq6ZA
#not ok#https://www.carhartt-wip.com/en/men-featured-9/og-detroit-jacket-winter-malbec-black-aged-canvas-964_1
#ok#https://itkkit.com/catalog/product/246455_thisisneverthat-regular-jeans-red/
#не дает цену#https://www.drmartens.com/eu/en_eu/sinclair-milled-nappa-leather-platform-boots-black/p/22564001
#ok#https://fuckthepopulation.com/collections/shop/products/made-in-hell-leather-puffer-coatwhite
#не дает цену#https://dimemtl.com/collections/dime-fall-24/products/fa24-coverstitch-sherpa-fleece-military-brown
#ok#https://kith.com/collections/mens-footwear/products/aaih3432

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import re

ua = UserAgent()
headers = {'User-Agent': ua.random}
url = "https://dimemtl.com/collections/dime-fall-24/products/fa24-coverstitch-sherpa-fleece-military-brown"

try:
    response = requests.get(url, headers=headers, timeout=15)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')

        product_name_tag = soup.find('h1')
        if product_name_tag:
            product_name = product_name_tag.get_text(strip=True)
        else:
            product_name = "Name not found"
            print("Cannot found name in headers.")

        currency_symbols = r'£|\$|€|¥'
        product_price_tag = soup.find('span', string=lambda text: re.search(currency_symbols, text) if text else False)
        
        if product_price_tag:
            product_price_match = re.search(r'(\£|\$|€|¥)\s?\d+\.?\d*', product_price_tag.get_text(strip=True))
            if product_price_match:
                product_price = product_price_match.group(0)
            else:
                product_price = "Price not found"
                print("Cannot found price in headers.")
        else:
            product_price = "Price not found"
            print("Cannot found price in headers.")

        # Выводим результаты в консоль
        print(f"Name: {product_name}")
        print(f"Price: {product_price}")
    else:
        print("Cannot GET. ERROR:", response.status_code)
except requests.exceptions.Timeout:
    print("Timeout15sec(yoox??).")
