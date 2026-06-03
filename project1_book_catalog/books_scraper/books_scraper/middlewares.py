import csv
import os

from scrapy.exceptions import IgnoreRequest


class IncrementalMiddleware:

    def __init__(self):
        self.processed_urls = set()

        if os.path.exists("books.csv"):
            with open("books.csv", "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                for row in reader:
                    self.processed_urls.add(row["product_url"])

    def process_request(self, request, spider):

        if request.meta.get("is_filter") and request.url in self.processed_urls:
            raise IgnoreRequest()

        return None