import csv
import os


class BooksPipeline:

    def open_spider(self, spider):
        self.file_name = "books.csv"
        self.processed_urls = set()
        self.seen_rows = {}  # url -> row dict

        if os.path.exists(self.file_name):
            with open(self.file_name, "r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    url = row.get("product_url")
                    if url:
                        self.processed_urls.add(url)
                        self.seen_rows[url] = row

    def process_item(self, item, spider):
        url = item.get("product_url")
        if url:
            self.processed_urls.add(url)

        # Convert spider item keys to CSV columns.
        csv_row = {
            "title": item.get("title", ""),
            "price": item.get("price", ""),
            "availability": item.get("availability", item.get("availability", "")),
            "stock_quantity": item.get("inventory", item.get("stock_qty", "")),
            "rating": item.get("rating", ""),
            "category": item.get("category", ""),
            "product_url": item.get("product_url", ""),
            "image_url": item.get("image_url", ""),
        }

        if url:
            self.seen_rows[url] = csv_row

        return item

    def close_spider(self, spider):
        fieldnames = [
            "title",
            "price",
            "availability",
            "stock_quantity",
            "rating",
            "category",
            "product_url",
            "image_url",
        ]

        with open(self.file_name, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for url, row in self.seen_rows.items():
                writer.writerow(row)

