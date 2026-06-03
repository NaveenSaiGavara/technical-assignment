import scrapy


class BookItem(scrapy.Item):
    title = scrapy.Field()
    price = scrapy.Field()           # float, e.g. 51.77
    availability = scrapy.Field()    # str, e.g. "In stock"
    stock_qty = scrapy.Field()       # int or None
    rating = scrapy.Field()          # int 1-5
    category = scrapy.Field()
    product_url = scrapy.Field()
    image_url = scrapy.Field()
