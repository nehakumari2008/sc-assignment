# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class MidsouthItem(scrapy.Item):
    title = scrapy.Field()
    price = scrapy.Field()
    description = scrapy.Field()
    review = scrapy.Field()
    stock = scrapy.Field()
    manufacturer = scrapy.Field()
    delivery_info = scrapy.Field()

