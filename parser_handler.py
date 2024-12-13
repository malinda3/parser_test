from ProductParser import ProductParser

test = ProductParser('https://faworldentertainment.com/en-eu/collections/shirts/products/2025-dill-collage-long-sleeve-tee?variant=41905423056993')
product_info = test.get_product_info()
print(product_info)