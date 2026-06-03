BOT_NAME = "books_scraper"

SPIDER_MODULES = ["books_scraper.spiders"]
NEWSPIDER_MODULE = "books_scraper.spiders"

ROBOTSTXT_OBEY = False

CONCURRENT_REQUESTS = 64

DOWNLOAD_DELAY = 0

RETRY_ENABLED = True
RETRY_TIMES = 2

DOWNLOAD_TIMEOUT = 15


ITEM_PIPELINES = {
    "books_scraper.pipelines.BooksPipeline": 300,
}

DOWNLOADER_MIDDLEWARES = {
    "books_scraper.middlewares.IncrementalMiddleware": 543,
}

LOG_LEVEL = "INFO"

FEED_EXPORT_ENCODING = "utf-8"