import re

import scrapy


class BooksSpider(scrapy.Spider):
    """Scrapes https://books.toscrape.com/ and yields book items."""

    name = "books"
    allowed_domains = ["books.toscrape.com"]
    start_urls = ["https://books.toscrape.com/"]

    # Maps site rating text to numeric representation.
    rating_map = {
        "One": 1,
        "Two": 2,
        "Three": 3,
        "Four": 4,
        "Five": 5,
    }

    def parse(self, response: scrapy.http.Response):
        """Landing page -> follow each category."""

        # Example: <ul class="nav-list"> contains category links.
        categories = response.css("ul.nav-list li ul li a")

        for category in categories:
            category_name = category.css("::text").get("").strip()
            category_url = category.attrib.get("href")

            if not category_url:
                continue

            self.logger.debug(
                "Discovered category: name=%s url=%s", category_name, category_url
            )

            yield response.follow(
                category_url,
                callback=self.parse_category,
                meta={"category": category_name},
            )

    def parse_category(self, response: scrapy.http.Response):
        """Category page -> follow each book and paginate."""

        # Each book links to a product detail page.
        books = response.css("article.product_pod h3 a::attr(href)").getall()

        for book_url in books:
            yield response.follow(
                book_url,
                callback=self.parse_book,
                meta={
                    "category": response.meta.get("category"),
                    # Used by IncrementalMiddleware to optionally ignore already-seen URLs.
                    "is_filter": True,
                },
            )

        # Pagination: next page link (if present).
        next_page = response.css("li.next a::attr(href)").get()

        if next_page:
            yield response.follow(
                next_page,
                callback=self.parse_category,
                meta=response.meta,
            )

    def parse_book(self, response: scrapy.http.Response):
        """Product detail page -> extract book fields."""

        try:
            # Title
            title = response.css("div.product_main h1::text").get("").strip()

            # Price string on the page looks like: "£51.77".
            price_text = response.css("p.price_color::text").get("")
            try:
                price = float(re.sub(r"[^\d.]", "", price_text))
            except (TypeError, ValueError):
                price = 0.0

            # Availability text includes stock quantity, e.g.
            # "Availability: 20 available".
            availability_text = (
                " ".join(response.css("p.instock.availability::text").getall()).strip()
            )

            stock_match = re.search(r"(\d+)", availability_text)
            inventory = int(stock_match.group(1)) if stock_match else 0

            # Normalized availability for downstream CSV.
            availability = "instock" if inventory > 0 else "outofstock"

            # Rating uses CSS class names like: "star-rating Three".
            rating_class = response.css("p.star-rating::attr(class)").get("")
            rating_text = rating_class.split()[-1] if rating_class else ""
            rating = self.rating_map.get(rating_text, 0)

            # Category is carried via meta, but we also fall back to breadcrumb.
            category = response.meta.get("category")
            if not category:
                category = (
                    response.css("ul.breadcrumb li:nth-child(3) a::text").get("").strip()
                )

            image_src = response.css(".item.active img::attr(src)").get("")
            image_url = response.urljoin(image_src) if image_src else ""

            item = {
                "title": title,
                "price": price,
                # Note: pipelines.py expects `inventory` and `availability`.
                "inventory": inventory,
                "availability": availability,
                "rating": rating,
                "category": category or "",
                "product_url": response.url,
                "image_url": image_url,
            }

            # Keep logs recruiter-friendly: structured + without dumping the full dict.
            self.logger.info(
                "Parsed book: title=%r price=%s rating=%s inventory=%s category=%r url=%s",
                title,
                price,
                rating,
                inventory,
                category,
                response.url,
            )

            yield item

        except Exception as e:
            # Avoid noisy exception dumps; include enough context for debugging.
            self.logger.error(
                "Error parsing book page: url=%s error=%s", response.url, str(e)
            )

