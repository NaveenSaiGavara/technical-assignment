# Books Catalog Scraper (Scrapy)

This document describes the `BooksSpider` located at:

- `books_scraper/books_scraper/spiders/books_catalog.py`

It scrapes **https://books.toscrape.com/** and extracts structured book data from category listings and paginated product detail pages.

---

## High-level behavior

1. **Start URL**: `https://books.toscrape.com/`
2. **Discover categories** from the landing page.
3. For each category page:
   - Follow all product links on the current page.
   - Follow the **next** page link until pagination ends.
4. For each product page:
   - Extract title, price, availability, rating, category, product URL, and image URL.
   - Yield a dictionary (Scrapy item-like payload) consumed by the configured pipeline.

---

## Spider contract (what it yields)

The spider yields a dict with these keys:

- `title` (str)
- `price` (float)
- `inventory` (int) — extracted from the availability text
- `availability` (str) — normalized to `instock` / `outofstock`
- `rating` (int) — star rating as `1..5` (or `0` if unknown)
- `category` (str)
- `product_url` (str)
- `image_url` (str)

These fields match what `books_scraper/pipelines.py` writes to `books.csv`.

---

## File walkthrough: `books_catalog.py`

### `rating_map`

The site represents rating as a CSS class (e.g. `star-rating Three`).

```python
rating_map = {
    "One": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5,
}
```

### `parse(self, response)` — landing page

- Finds category links with:
  - CSS selector: `ul.nav-list li ul li a`
- For each category link:
  - `category_name` is extracted from the link text
  - `category_url` is extracted from the link `href`
- Follows the category URL and calls `parse_category`.

Recruiter-friendly logging:
- Uses `self.logger.debug(...)` to avoid spamming at normal log levels.

### `parse_category(self, response)` — category page + pagination

- Extracts product detail URLs with:
  - CSS selector: `article.product_pod h3 a::attr(href)`
- For each product URL:
  - Follows the product page and calls `parse_book`
  - Passes `meta={"category": <name>, "is_filter": True}`

Pagination:
- Follows `li.next a::attr(href)` if present.

### `parse_book(self, response)` — product detail page

All extraction happens inside a `try/except` so parsing failures do not crash the entire crawl.

Key fields:

- **Title**: `div.product_main h1::text`
- **Price**:
  - Reads `p.price_color::text` (e.g. `£51.77`)
  - Strips currency symbols using regex: `re.sub(r"[^\d.]", "", price_text)`
  - Converts to `float` with safe fallback to `0.0`
- **Availability / inventory**:
  - Reads availability text fragments: `p.instock.availability::text`
  - Extracts the first integer via regex: `re.search(r"(\d+)", availability_text)`
  - Normalizes to `availability = "instock" if inventory > 0 else "outofstock"`
- **Rating**:
  - Reads `p.star-rating::attr(class)` which typically includes `star-rating <Word>`
  - Uses `rating_class.split()[-1]` to map it via `rating_map`
- **Category**:
  - Primarily comes from `response.meta["category"]`
  - Falls back to breadcrumb selector: `ul.breadcrumb li:nth-child(3) a::text`
- **Image URL**:
  - Reads `.item.active img::attr(src)`
  - Uses `response.urljoin(...)` to create an absolute URL

Logging:
- Logs one line per successful book parse:
  - `Parsed book: title=... price=... rating=... inventory=... category=... url=...`

Errors:
- Logs parsing errors with:
  - `Error parsing book page: url=<...> error=<...>`

---

## Incremental scraping support

Your project includes `books_scraper/middlewares.py` with `IncrementalMiddleware`.

- When category traversal follows product pages, the spider sets:
  - `meta["is_filter"] = True`

The middleware can then ignore requests whose `product_url` already exists in `books.csv`.

---

## How to run

From `project1_book_catalog/books_scraper`:

```bash
pip install -r requirements.txt
scrapy crawl books_catalog
```

Optional (based on your `README.md`):

```bash
scrapy crawl books_catalog --loglevel=DEBUG
```