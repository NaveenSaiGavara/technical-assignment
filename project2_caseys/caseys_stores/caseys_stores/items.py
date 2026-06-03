import scrapy


class CaseysStoresItem(scrapy.Item):
    ADDRESS = scrapy.Field()
    CITY = scrapy.Field()
    STATE = scrapy.Field()
    ZIP = scrapy.Field()
    COUNTRY = scrapy.Field()

    LAT = scrapy.Field()
    LONG = scrapy.Field()

    STORE_ID = scrapy.Field()

    FUELTYPE = scrapy.Field()
    FUELPRICE = scrapy.Field()

    BRAND = scrapy.Field()

    SCRAPPED_DATE = scrapy.Field()

