import scrapy
from scrapy.selector import Selector
import logging
import html2text
import requests
import json

class ShootersupplySpider(scrapy.Spider):
    name = 'shootersupply'
    allowed_domains = ['midsouthshooterssupply.com']
    start_urls = ['https://www.midsouthshooterssupply.com/dept/reloading/primers']
    base_url = "https://www.midsouthshooterssupply.com"
    items_found = []

    #  Create empty Json file to store json output
    json_file_name = 'output.json'
    with open(json_file_name, mode='w', encoding='utf-8') as f:
        json.dump([], f)

    # 1st level parse to find the URL for all items on the first page
    # I have not added logic for navigating to other pages
    def parse(self, response):
        logging.info("Crawling Midsouth...")
        sel = Selector(response)

        products = sel.xpath('//*[@id="Div1"]')
        for product in products:
            # This works reliably in xpath but not in CSS selector
            product_uri = product.xpath('a/@href').extract()[0]
            product_absolute_url = self.base_url + product_uri
            print(product_absolute_url)
            # For each product found I am initiating a new Scrapy request with url of that product
            yield scrapy.Request(product_absolute_url, self.parse_item)

    # 2nd Level parse for the product page. Here I am using CSS selectors to find the info for all the products
    def parse_item(self, response):
        sel = Selector(response)
        item = {}
        item['title'] = sel.css('#product-main > div.product-heading > h1::text').get()
        item['price'] = sel.css('#product-main > div.product-info > div.offer > span > span::text').get()
        item['description'] = self.get_description(sel)
        item['in_stock'] = self.get_stock(sel)
        item['manufacturer'] = sel.css('#product-main > div.product-heading > div > span:nth-child(1) > a::text').get()
        item['delivery_info'] = self.get_delivery_info(sel)
        item['reviews'] = self.get_reviews(response.url)

        # Open the initialized json file from disk
        with open(self.json_file_name, mode='r', encoding='utf-8') as f:
            # Convert json to python List
            json_items = json.load(f)
        # Append item dictionary to the
        with open(self.json_file_name, mode='w', encoding='utf-8') as f:
            # Append to the list
            json_items.append(item)
            # Convert python list to json and write to the file
            json.dump(json_items, f)

    def get_description(self, selector):
        raw_description = selector.css('#description').get()
        h = html2text.HTML2Text()
        # This output is markdown. Which works great as it is. But since assignment required to convert
        # spaces with '_' I am doing it. But I highly recommend using default HTML2Text markdown output
        text_description = h.handle(raw_description)
        text_description_removed_newline = text_description.replace('\n', '_')
        return text_description_removed_newline

    def get_stock(self, sel):
        stock_text_status= sel.css('#product-main > div.product-info > span > span::text').get()
        if stock_text_status in 'Out of Stock':
            return False
        elif stock_text_status in 'In Stock':
            return True
        else:
            return "Unable to find stock status"

    def get_delivery_info(self, sel):
        raw_delivery_info = sel.css('#delivery-info').get()
        h = html2text.HTML2Text()
        # This output is markdown. Which works great as it is. But since assignment required to convert
        # spaces with '_' I am doing it. But I highly recommend using default HTML2Text markdown output
        text_delivery_info = h.handle(raw_delivery_info)
        text_delivery_info_remove_newline = text_delivery_info.replace('\n', '_')
        return text_delivery_info_remove_newline

    # Reviews are provided via a json api to the website so it cannot be loaded via scrapy directly
    # I am using python requests package to load the requests api
    def get_reviews(self, item_url):
        # Find the item id by splitting on '/'
        item_id = item_url.split('/')[4]
        review_provider_url = self.get_review_provider_url(item_id)

        # These headers are pulled from Chrome using copy as cURL and converting it to python
        headers = {
            'authority': 'display.powerreviews.com',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="99", "Google Chrome";v="99"',
            'sec-ch-ua-mobile': '?0',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36',
            'sec-ch-ua-platform': '"Windows"',
            'accept': '*/*',
            'origin': 'https://www.midsouthshooterssupply.com',
            'sec-fetch-site': 'cross-site',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'referer': 'https://www.midsouthshooterssupply.com/',
            'accept-language': 'en-US,en;q=0.9,kn;q=0.8',
        }

        response = requests.get(review_provider_url, headers=headers)
        # Here since the reviews response is already json  I am attaching as it is to our reviews field
        json_response = response.json()
        reviews = json_response['results'][0]['reviews']
        return reviews

    # This review url was found by looking in chrome requests
    def get_review_provider_url(self, item_id):
        return "https://display.powerreviews.com/m/440705/l/en_US/product/" + item_id + "/reviews?apikey=dafd221f-f51b-4f57-98e9-7ed9603a9576&_noconfig=true"



