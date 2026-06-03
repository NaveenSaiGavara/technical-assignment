# Caseys Stores Scraper (Scrapy)

This project contains a Scrapy spider that scrapes Casey’s store information (address/geo and fuel-related offer data) by combining:

1. **Radar autocomplete API** (to turn a city/state/ZIP string into latitude/longitude)
2. **Casey’s GraphQL endpoint** (to fetch stores near those coordinates)
3. **Casey’s store detail pages** (to extract structured JSON-LD data about the business and fuel offers)

The output is a CSV produced via Scrapy’s feed exports.

## What the spider does (high level)

For each configured location in `CaseysSpider.locations`:

1. **`start()`**
   - Builds a Radar URL for an autocomplete query.
   - Yields a `GET` request to `api.radar.io`.

2. **`parse_location()`**
   - Parses the Radar JSON response.
   - Extracts the first match’s `latitude` and `longitude`.
   - Sends a `POST` request to Caseys GraphQL with payload:
     - `operationName = GetStoresByFilters`
     - `occasionType = CARRYOUT`
     - `withTimeSlots = true`

3. **`parse_store_search()`**
   - Parses GraphQL JSON response.
   - For each returned store, schedules a request to the store’s `locationUrl`.

4. **`parse_store()`**
   - Extracts all `script[type="application/ld+json"]` blocks.
   - Loads each script as JSON until it finds a dictionary whose `@type` is `LocalBusiness`.
   - From that JSON-LD payload, yields a `CaseysStoresItem` for each offer in `makesOffer`.

5. **`errback_log()`**
   - Centralized request failure logging.

## Output schema

Items are defined in `project2_caseys/caseys_stores/items.py` as `CaseysStoresItem` with fields:

- `ADDRESS`, `CITY`, `STATE`, `ZIP`, `COUNTRY`
- `LAT`, `LONG`
- `STORE_ID`
- `FUELTYPE`, `FUELPRICE`
- `BRAND`
- `SCRAPPED_DATE`

Each store page can contain multiple offers; this spider yields one item **per offer**.

## Logging & reliability

The spider uses Scrapy’s `self.logger` for:
- Lifecycle logs (spider start)
- Validation logs (missing coordinates, empty store results)
- Error logs with stack traces via `logger.exception(...)`

It also configures retry behavior in `custom_settings` on the spider:
- Retries enabled
- Retry on typical transient HTTP status codes (403/429/5xx)
- Request timeouts and basic throttling

## Running the spider

From the `project2_caseys` folder:

```bash
scrapy crawl caseys -O output/caseys_locations.csv
```
