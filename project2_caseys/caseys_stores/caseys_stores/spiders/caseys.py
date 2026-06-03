"""Caseys Stores spider.

This spider:
1) Uses Radar's autocomplete API to geocode a list of store locations.
2) Calls Casey's GraphQL endpoint to retrieve nearby stores.
3) Visits each store's detail page and extracts JSON-LD (LocalBusiness) data.
4) Emits one item per offer (makesOffer) with address/geo + fuel offer data.

Design goals:
- Clear logging for recruiter-friendly readability
- Defensive parsing and robust error handling
- Small, well-scoped parsing steps

Note: The Radar API Authorization token is embedded in spider headers in this
exercise. In production, move it to environment variables / secrets.
"""
import json
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import quote, urljoin

import scrapy

from caseys_stores.items import CaseysStoresItem


class CaseysSpider(scrapy.Spider):
    """Scrapy spider to collect Casey's store and fuel offer information."""

    name = "caseys"
    allowed_domains = ["api.radar.io", "caseys.com"]

    # Starter set of crawl targets (can be expanded).
    locations: List[str] = [
        "Springdale, AR 72764",
        "Cedar Rapids, IA 52404-5025",
        "Hinckley, IL 60520",
        "Cimarron, KS 67835",
    ]

    # Request headers for Radar autocomplete.
    radar_headers: Dict[str, str] = {
        # Token is embedded for this assessment task.
        "Authorization": "prj_live_pk_694c771a37730b9c4dbd544494f9e79ca214d033",
        "X-Radar-Device-Type": "Web",
        "X-Radar-SDK-Version": "5.1.0",
        "Accept": "application/json",
        "Origin": "https://www.caseys.com",
        "Referer": "https://www.caseys.com/",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
    }

    # Request headers for Casey's GraphQL endpoint.
    caseys_headers: Dict[str, str] = {
        "Content-Type": "application/json",
        "Accept": "*/*",
        "Origin": "https://www.caseys.com",
        "Referer": "https://www.caseys.com/locations",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
    }

    # Request headers for store HTML pages.
    html_headers: Dict[str, str] = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
    }

    graphql_url = "https://www.caseys.com/api/graphql"

    # GraphQL query used by the spider.
    graphql_query = """
    query GetStoresByFilters(
        $input: StoresByCoordinateInput!,
        $occasionType: OccasionType!,
        $withTimeSlots: Boolean!
    ) {
        storesByCoordinate(input: $input) {
            store {
                storeNumber
                brand
                locationUrl
                address {
                    line1
                    city
                    stateAbbreviation
                    postalCode
                    phoneNumber
                }
                geoPoint {
                    latitude
                    longitude
                }
            }
        }
    }
    """

    # Spider-level overrides for retries/timeouts/concurrency.
    # (These are intentionally placed on the spider for easy review.)
    custom_settings = {
        "ITEM_PIPELINES": {
            "caseys_stores.pipelines.CaseysStoresPipeline": 300,
        },
        "ROBOTSTXT_OBEY": False,
        "RETRY_ENABLED": True,
        "RETRY_TIMES": 4,
        "RETRY_HTTP_CODES": [403, 408, 429, 500, 502, 503, 504],
        "DOWNLOAD_TIMEOUT": 30,
        "DOWNLOAD_DELAY": 0.4,
        "CONCURRENT_REQUESTS": 4,
        "LOG_LEVEL": "INFO",
    }

    def start_requests(self) -> Iterable[scrapy.Request]:
        """Generate initial Radar requests for configured target locations."""

        self.logger.info("Starting Casey's spider")

        for location in self.locations:
            url = (
                "https://api.radar.io/v1/search/autocomplete"
                f"?query={quote(location)}"
                "&limit=8"
                "&layers=address,state,postalCode,locality"
                "&countryCode=US"
            )

            self.logger.info("Requesting coordinates for: %s", location)

            yield scrapy.Request(
                url=url,
                method="GET",
                headers=self.radar_headers,
                callback=self.parse_location,
                cb_kwargs={"location": location},
                errback=self.errback_log,
                dont_filter=True,
            )

    def parse_location(self, response: scrapy.http.Response, location: str) -> Iterable[scrapy.Request]:
        """Parse Radar response to extract lat/lon, then call GraphQL."""

        try:
            if response.status != 200:
                self.logger.error(
                    "Radar request failed for %s. Status: %s", location, response.status
                )
                return

            data = json.loads(response.text)
            addresses = data.get("addresses", [])

            if not addresses:
                self.logger.warning("No coordinates found for location: %s", location)
                return

            latitude = addresses[0].get("latitude")
            longitude = addresses[0].get("longitude")

            if latitude is None or longitude is None:
                self.logger.warning(
                    "Latitude/Longitude missing for location: %s", location
                )
                return

            # Build GraphQL payload.
            payload: Dict[str, Any] = {
                "operationName": "GetStoresByFilters",
                "variables": {
                    "input": {
                        "latitude": str(latitude),
                        "longitude": str(longitude),
                    },
                    "occasionType": "CARRYOUT",
                    "withTimeSlots": True,
                },
                "query": self.graphql_query,
            }

            self.logger.info(
                "Geocoded %s -> (lat=%s, lon=%s). Fetching stores via GraphQL.",
                location,
                latitude,
                longitude,
            )

            yield scrapy.Request(
                url=self.graphql_url,
                method="POST",
                headers=self.caseys_headers,
                body=json.dumps(payload),
                callback=self.parse_store_search,
                errback=self.errback_log,
                dont_filter=True,
            )

        except json.JSONDecodeError as exc:
            self.logger.exception("Invalid JSON from Radar for %s: %s", location, exc)
        except Exception as exc:
            self.logger.exception("Error parsing coordinates for %s: %s", location, exc)

    def parse_store_search(self, response: scrapy.http.Response) -> Iterable[scrapy.Request]:
        """Parse GraphQL response and schedule store page requests."""

        try:
            if response.status != 200:
                self.logger.error(
                    "GraphQL request failed. Status: %s", response.status
                )
                return

            data = json.loads(response.text)

            stores = (
                data.get("data", {})
                .get("storesByCoordinate", [])
            )

            if not stores:
                self.logger.warning("No stores returned from GraphQL response")
                return

            for store_data in stores:
                store = store_data.get("store", {})
                location_url = store.get("locationUrl")

                if not location_url:
                    self.logger.debug("Skipping store without locationUrl: %s", store)
                    continue

                url = urljoin("https://www.caseys.com", location_url)

                yield scrapy.Request(
                    url=url,
                    callback=self.parse_store,
                    meta={"store": store},
                    errback=self.errback_log,
                    headers=self.html_headers,
                    dont_filter=True,
                )

        except json.JSONDecodeError as exc:
            self.logger.exception("Invalid JSON from GraphQL: %s", exc)
        except Exception as exc:
            self.logger.exception("Error parsing GraphQL response: %s", exc)

    def _extract_localbusiness_jsonld(self, response: scrapy.http.Response) -> Optional[Dict[str, Any]]:
        """Return the JSON-LD dict for the LocalBusiness block, if present."""

        scripts = response.css('script[type="application/ld+json"]::text').getall()

        for script in scripts:
            if not script or not script.strip():
                continue

            try:
                data = json.loads(script.strip())

                # We expect JSON-LD objects; sometimes it can be a list.
                if isinstance(data, dict) and data.get("@type") in {"LocalBusiness"}:
                    return data

                # If the site ever emits a list, attempt to find LocalBusiness inside.
                if isinstance(data, list):
                    for entry in data:
                        if isinstance(entry, dict) and entry.get("@type") in {"LocalBusiness"}:
                            return entry

            except json.JSONDecodeError:
                # Keep scanning other scripts.
                continue

        return None

    def parse_store(self, response: scrapy.http.Response) -> Iterable[CaseysStoresItem]:
        """Extract JSON-LD and emit one item per offer."""

        try:
            store: Dict[str, Any] = response.meta.get("store", {})

            json_ld = self._extract_localbusiness_jsonld(response)
            if not json_ld:
                self.logger.warning("JSON-LD not found (LocalBusiness) for: %s", response.url)
                return

            address = json_ld.get("address", {})
            geo = json_ld.get("geo", {})
            offers = json_ld.get("makesOffer", [])
            scrape_date = date.today().isoformat()

            self.logger.info(
                "Scraping store page %s (offers=%s)", response.url, len(offers) if isinstance(offers, list) else "?"
            )

            # Defensive: makesOffer sometimes can be dict; normalize to list.
            if isinstance(offers, dict):
                offers = [offers]

            for offer in offers:
                if not isinstance(offer, dict):
                    continue

                yield CaseysStoresItem(
                    ADDRESS=address.get(
                        "streetAddress",
                        store.get("address", {}).get("line1", ""),
                    ),
                    CITY=address.get(
                        "addressLocality",
                        store.get("address", {}).get("city", ""),
                    ),
                    STATE=address.get(
                        "addressRegion",
                        store.get("address", {}).get("stateAbbreviation", ""),
                    ),
                    ZIP=address.get(
                        "postalCode",
                        store.get("address", {}).get("postalCode", ""),
                    ),
                    COUNTRY="USA",
                    LAT=geo.get(
                        "latitude",
                        store.get("geoPoint", {}).get("latitude", ""),
                    ),
                    LONG=geo.get(
                        "longitude",
                        store.get("geoPoint", {}).get("longitude", ""),
                    ),
                    STORE_ID=json_ld.get(
                        "branchCode",
                        store.get("storeNumber", ""),
                    ),
                    FUELTYPE=offer.get("name", ""),
                    FUELPRICE=offer.get("price", ""),
                    BRAND=store.get("brand", "Casey's"),
                    SCRAPPED_DATE=scrape_date,
                )

        except Exception as exc:
            self.logger.exception("Error parsing store page %s: %s", response.url, exc)

    def errback_log(self, failure):
        """Centralized errback to log request failures."""

        request = getattr(failure, "request", None)
        url = getattr(request, "url", "<unknown>")

        self.logger.error("Request failed: %s", url)
        self.logger.error(repr(failure))

