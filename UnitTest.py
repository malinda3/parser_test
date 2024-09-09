import pytest
from bs4 import BeautifulSoup
from ProductParser import ProductParser
import requests

def test_fetch_page_failure(mocker):
    # Simulating a failed HTTP request
    mocker.patch('requests.get', side_effect=Exception("Network Error"))
    
    parser = ProductParser("http://example.com")
    parser.fetch_page()

    assert parser.soup is None

def test_parse_product_name_not_found():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><div>No product name here</div></html>', 'html.parser')
    parser.parse_product_name()

    assert parser.product_name == "Name not found"

def test_parse_product_price_different_currency():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><span>€99.99</span></html>', 'html.parser')
    parser.parse_product_price()

    assert parser.product_price == "€99.99"

def test_parse_product_price_with_whitespace():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><span> $ 123.45 </span></html>', 'html.parser')
    parser.parse_product_price()

    assert parser.product_price == "$123.45"

def test_parse_product_price_with_text():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><span>Price: $123.45</span></html>', 'html.parser')
    parser.parse_product_price()

    assert parser.product_price == "$123.45"

def test_parse_product_price_with_comma_separator():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><span>£1,234.56</span></html>', 'html.parser')
    parser.parse_product_price()

    assert parser.product_price == "£1,234.56"

def test_parse_product_price_invalid_format():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><span>ABC123.45</span></html>', 'html.parser')
    parser.parse_product_price()

    assert parser.product_price == "Price not found"

def test_parse_product_price_multiple_prices():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><span>$123.45</span><span>€99.99</span></html>', 'html.parser')
    parser.parse_product_price()

    assert parser.product_price == "$123.45"

def test_parse_product_name_and_price():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><h1>Test Product</h1><span>$123.45</span></html>', 'html.parser')
    parser.parse_product_name()
    parser.parse_product_price()

    assert parser.product_name == "Test Product"
    assert parser.product_price == "$123.45"

def test_parse_product_price_no_soup():
    parser = ProductParser("http://example.com")
    parser.soup = None
    parser.parse_product_price()

    assert parser.product_price == "Price not found"

def test_fetch_page_timeout(mocker):
    mocker.patch('requests.get', side_effect=requests.exceptions.Timeout)
    
    parser = ProductParser("http://example.com")
    parser.fetch_page()

    assert parser.soup is None

def test_fetch_page_404(mocker):
    mock_response = mocker.Mock()
    mock_response.status_code = 404
    mocker.patch('requests.get', return_value=mock_response)
    
    parser = ProductParser("http://example.com")
    parser.fetch_page()

    assert parser.soup is None

def test_parse_product_name_with_special_chars():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><h1>Product @#%$</h1></html>', 'html.parser')
    parser.parse_product_name()
    
    assert parser.product_name == "Product @#%$"

def test_parse_product_price_with_currency_code():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><span>USD 123.45</span></html>', 'html.parser')
    parser.parse_product_price()
    
    assert parser.product_price == "USD 123.45"

def test_parse_product_price_with_no_sign():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><span>123.45</span></html>', 'html.parser')
    parser.parse_product_price()
    
    assert parser.product_price == "Price not found"

def test_parse_product_price_with_multiple_spaces():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><span>$    123.45</span></html>', 'html.parser')
    parser.parse_product_price()
    
    assert parser.product_price == "$123.45"

def test_parse_product_price_with_decimal_separator_comma():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><span>€123,45</span></html>', 'html.parser')
    parser.parse_product_price()
    
    assert parser.product_price == "€123,45"

def test_parse_product_name_case_insensitive():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><h1>TeSt PrOdUcT</h1></html>', 'html.parser')
    parser.parse_product_name()
    
    assert parser.product_name == "TeSt PrOdUcT"

def test_parse_product_price_with_percent_sign():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><span>$123.45%</span></html>', 'html.parser')
    parser.parse_product_price()
    
    assert parser.product_price == "$123.45%"

def test_parse_product_price_with_brackets():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><span>($123.45)</span></html>', 'html.parser')
    parser.parse_product_price()
    
    assert parser.product_price == "($123.45)"

def test_parse_product_name_with_numbers():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><h1>Product 123</h1></html>', 'html.parser')
    parser.parse_product_name()
    
    assert parser.product_name == "Product 123"

def test_parse_product_price_with_date():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><span>$123.45 (2024)</span></html>', 'html.parser')
    parser.parse_product_price()
    
    assert parser.product_price == "$123.45"

def test_parse_product_price_with_usd_and_other_currency():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><span>$123.45 / €99.99</span></html>', 'html.parser')
    parser.parse_product_price()
    
    assert parser.product_price == "$123.45"

def test_parse_product_name_with_newlines():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><h1>Product\nName</h1></html>', 'html.parser')
    parser.parse_product_name()
    
    assert parser.product_name == "Product Name"

def test_parse_product_price_with_single_value():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><span>$123</span></html>', 'html.parser')
    parser.parse_product_price()
    
    assert parser.product_price == "$123"

def test_parse_product_price_with_different_currency_order():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><span>123.45 $</span></html>', 'html.parser')
    parser.parse_product_price()
    
    assert parser.product_price == "$123.45"

def test_parse_product_name_with_html_entities():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><h1>Product &amp; Name</h1></html>', 'html.parser')
    parser.parse_product_name()
    
    assert parser.product_name == "Product & Name"

def test_parse_product_price_with_large_number():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><span>$1,000,000.00</span></html>', 'html.parser')
    parser.parse_product_price()
    
    assert parser.product_price == "$1,000,000.00"

def test_parse_product_price_with_different_span_tags():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><div><span>$123.45</span></div></html>', 'html.parser')
    parser.parse_product_price()
    
    assert parser.product_price == "$123.45"

def test_parse_product_name_with_cyrillic_characters():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><h1>Товар</h1></html>', 'html.parser')
    parser.parse_product_name()
    
    assert parser.product_name == "Товар"

def test_parse_product_price_with_other_symbols():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><span>$123.45*</span></html>', 'html.parser')
    parser.parse_product_price()
    
    assert parser.product_price == "$123.45*"

def test_parse_product_name_with_html_tags():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><h1><b>Product Name</b></h1></html>', 'html.parser')
    parser.parse_product_name()
    
    assert parser.product_name == "Product Name"

def test_parse_product_price_with_spaces_and_special_chars():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><span>$ 1,234.56! </span></html>', 'html.parser')
    parser.parse_product_price()
    
    assert parser.product_price == "$1,234.56!"

def test_parse_product_price_with_non_numeric_price():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><span>$N/A</span></html>', 'html.parser')
    parser.parse_product_price()
    
    assert parser.product_price == "Price not found"

def test_parse_product_price_with_only_currency_sign():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><span>$</span></html>', 'html.parser')
    parser.parse_product_price()
    
    assert parser.product_price == "Price not found"

def test_parse_product_name_with_html_comments():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><!-- Product Name --><h1>Product Name</h1></html>', 'html.parser')
    parser.parse_product_name()
    
    assert parser.product_name == "Product Name"

def test_parse_product_price_with_different_amounts():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><span>$1</span><span>$2</span><span>$3</span></html>', 'html.parser')
    parser.parse_product_price()
    
    assert parser.product_price == "$1"

def test_parse_product_price_with_fallback_to_alternative_span():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><div><span>$123.45</span></div></html>', 'html.parser')
    parser.parse_product_price()
    
    assert parser.product_price == "$123.45"

def test_parse_product_name_empty_string():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><h1></h1></html>', 'html.parser')
    parser.parse_product_name()
    
    assert parser.product_name == "Name not found"

def test_parse_product_name_with_large_text():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><h1>' + 'A' * 1000 + '</h1></html>', 'html.parser')
    parser.parse_product_name()
    
    assert parser.product_name == 'A' * 1000

def test_parse_product_price_with_large_numbers():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><span>$10,000,000.00</span></html>', 'html.parser')
    parser.parse_product_price()
    
    assert parser.product_price == "$10,000,000.00"

def test_parse_product_price_with_minimal_amount():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><span>$0.01</span></html>', 'html.parser')
    parser.parse_product_price()
    
    assert parser.product_price == "$0.01"

def test_parse_product_price_with_no_price_tag():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><div>No price tag here</div></html>', 'html.parser')
    parser.parse_product_price()
    
    assert parser.product_price == "Price not found"

def test_parse_product_price_with_alternating_currency_symbols():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><span>$123.45 €99.99</span></html>', 'html.parser')
    parser.parse_product_price()
    
    assert parser.product_price == "$123.45"

def test_parse_product_name_with_unexpected_html_structure():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><div><h1><span>Product Name</span></h1></div></html>', 'html.parser')
    parser.parse_product_name()
    
    assert parser.product_name == "Product Name"

def test_parse_product_price_with_non_standard_currency_symbols():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><span>₹123.45</span></html>', 'html.parser')
    parser.parse_product_price()
    
    assert parser.product_price == "₹123.45"

def test_parse_product_price_with_escaped_html_characters():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><span>&#36;123.45</span></html>', 'html.parser')
    parser.parse_product_price()
    
    assert parser.product_price == "$123.45"

def test_parse_product_price_with_decimal_separator_period():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><span>123.45%</span></html>', 'html.parser')
    parser.parse_product_price()
    
    assert parser.product_price == "123.45%"

def test_parse_product_name_with_double_spaces():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><h1>Product  Name</h1></html>', 'html.parser')
    parser.parse_product_name()
    
    assert parser.product_name == "Product  Name"

def test_parse_product_price_with_custom_html_entity():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><span>&dollar;123.45</span></html>', 'html.parser')
    parser.parse_product_price()
    
    assert parser.product_price == "$123.45"

def test_parse_product_name_with_tags_in_value():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><h1><b>Product Name</b></h1></html>', 'html.parser')
    parser.parse_product_name()
    
    assert parser.product_name == "Product Name"

def test_parse_product_price_with_negative_value():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><span>-$123.45</span></html>', 'html.parser')
    parser.parse_product_price()
    
    assert parser.product_price == "-$123.45"

def test_parse_product_price_with_exponential_notation():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><span>$1e3</span></html>', 'html.parser')
    parser.parse_product_price()
    
    assert parser.product_price == "$1e3"

def test_parse_product_name_with_multiline_text():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><h1>Product\nName\nNew Line</h1></html>', 'html.parser')
    parser.parse_product_name()
    
    assert parser.product_name == "Product Name New Line"

def test_parse_product_price_with_unexpected_currency_format():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><span>£ 123.45 </span></html>', 'html.parser')
    parser.parse_product_price()
    
    assert parser.product_price == "£123.45"

def test_parse_product_name_with_nested_tags():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><h1><span>Product</span> Name</h1></html>', 'html.parser')
    parser.parse_product_name()
    
    assert parser.product_name == "Product Name"

def test_parse_product_price_with_currency_in_subscript():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><span>$<sub>123.45</sub></span></html>', 'html.parser')
    parser.parse_product_price()
    
    assert parser.product_price == "$123.45"

def test_parse_product_name_with_emoji():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><h1>Product 🚀</h1></html>', 'html.parser')
    parser.parse_product_name()
    
    assert parser.product_name == "Product 🚀"

def test_parse_product_price_with_currency_and_percentage():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><span>$123.45 (20% off)</span></html>', 'html.parser')
    parser.parse_product_price()
    
    assert parser.product_price == "$123.45"

def test_parse_product_name_with_single_character():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><h1>A</h1></html>', 'html.parser')
    parser.parse_product_name()
    
    assert parser.product_name == "A"

def test_parse_product_price_with_multi_currency_symbols():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><span>€100, $120</span></html>', 'html.parser')
    parser.parse_product_price()
    
    assert parser.product_price == "€100"

def test_parse_product_name_with_no_h1_tag():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><div><p>Product Name</p></div></html>', 'html.parser')
    parser.parse_product_name()
    
    assert parser.product_name == "Name not found"

def test_parse_product_price_with_large_price():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><span>$999,999.99</span></html>', 'html.parser')
    parser.parse_product_price()
    
    assert parser.product_price == "$999,999.99"

def test_parse_product_name_with_special_characters_only():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><h1>!@#$%^&*</h1></html>', 'html.parser')
    parser.parse_product_name()
    
    assert parser.product_name == "!@#$%^&*"

def test_parse_product_price_with_only_cents():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><span>$0.99</span></html>', 'html.parser')
    parser.parse_product_price()
    
    assert parser.product_price == "$0.99"

def test_parse_product_name_with_no_spaces():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><h1>ProductName</h1></html>', 'html.parser')
    parser.parse_product_name()
    
    assert parser.product_name == "ProductName"

def test_parse_product_price_with_russian_currency():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><span>₽123.45</span></html>', 'html.parser')
    parser.parse_product_price()
    
    assert parser.product_price == "₽123.45"

def test_parse_product_name_with_html_entities_in_name():
    parser = ProductParser("http://example.com")
    parser.soup = BeautifulSoup('<html><h1>Product &amp; Name</h1></html>', 'html.parser')
    parser.parse_product_name()
    
    assert parser.product_name == "Product & Name"