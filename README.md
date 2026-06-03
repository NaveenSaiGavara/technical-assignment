# Assessment Project Submission

This repository contains solutions and supporting materials for the three assessment projects.

## Project 1 — Book Catalog Scraping (books.toscrape.com)
### Status
✅ Completed

### Deliverables
- Scrapy spider implementation
- CSV output (`books.csv`)
- Data extraction pipeline
- Incremental crawling support

### Implemented Features
- Category traversal
- Pagination handling
- Product extraction
- Price normalization
- Rating normalization
- Availability conversion (`instock` / `outofstock`)
- CSV export
- Incremental duplicate avoidance

### Output
The spider successfully generated the required output dataset and meets the project requirements.

---

## Project 2 — Casey’s Store & Fuel Price Scraping
### Status
⚠️ Code Completed, Output Validation Blocked

### Work Completed
- Store discovery workflow implemented
- Fuel price extraction logic implemented
- End-to-end Scrapy spider developed
- CSV export pipeline implemented
- Data parsing and normalization completed
- Multiple approaches attempted to retrieve required data

### Approaches Attempted
The target website appears to be protected by Cloudflare and consistently returned HTTP 403 responses during testing.

- **Scrapy (standard + custom headers + fingerprinting):** HTTP 403 Forbidden
- **curl_cffi (impersonation + HTTP/1.1/HTTP/2 variations):** HTTP 403 Forbidden
- **Playwright (browser automation + JS rendering):** still blocked by protection
- **Additional techniques (header rotation, sessions, cookies, user-agent changes):** still blocked

### Blocker Encountered
Without access to a suitable proxy infrastructure capable of passing Cloudflare validation, it was not possible to verify successful data extraction against a production request flow.

### Deliverables
- **Completed:** full scraper implementation + extraction logic
- **Not Completed:** final validated output dataset matching the expected submission format

---

## Project 3 — Fuel Rewards® Mobile App API Discovery
### Status
⚠️ Attempted but Not Completed

### Objective
Identify and document the API endpoints used by the Fuel Rewards® Android application to retrieve location and fuel-related information.

### Required Deliverables (Not Completed)
- API endpoint(s)
- Request headers
- Parameters
- Payloads
- Sample response JSON
- Discovery methodology with evidence (screenshots)
- Sample output for coordinates:
  - Latitude: 42.78123786
  - Longitude: -88.06284121

### Environment Setup
- Genymotion Android 11 (Pixel 5)
- Root access enabled
- Frida + Objection tooling attempted

### Testing Performed (Summary)
- Older APK versions: forced upgrade to latest
- Latest APK: crash on emulator (“Fuel Rewards keeps stopping”)
- Manual Activity launch: crash during SplashActivity
- Frida/Objection: instrumentation-related crashes (e.g., IllegalMonitorStateException)
- Physical device: app runs, but requires authentication; unable to proceed to location/fuel search

### Conclusion
API discovery could not be completed due to emulator/app crashes and lack of authenticated access on the physical device.

### Evidence
Details documented in `project3_fuel_reward_app/findings`.

---

## Final Summary
| Project | Status |
|---|---|
| Project 1 — Book Catalog Scraping | ✅ Completed |
| Project 2 — Casey’s Store & Fuel Price Scraping | ⚠️ Code completed, output validation blocked |
| Project 3 — Fuel Rewards® API Discovery | ⚠️ Attempted, blocked by environment/application constraints |

