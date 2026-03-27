# Changelog

## [2.1.0] - 2026-03-26
### Security
- Strip and validate API token on entry (removes accidental whitespace before storage; rejects blank input)
- Redacted full DNS record objects from debug logs to avoid exposing Cloudflare record IDs
- Removed raw exception message from `UpdateFailed` to prevent API response bodies leaking into HA logs and the UI error banner
- Replaced `asyncio.gather(*tasks)` with `return_exceptions=True` so all update tasks always run to completion before any exception is re-raised

## [2.0.1] - 2026-03-26
### Added
- Cloudflare integration icon (`icon.png`) for HA integration card and HACS store

## [2.0.0] - 2026-03-26
### Changed
- Version bump to 2.0.0 reflecting the significant feature additions over the original single-zone integration
- Added Apache 2.0 LICENSE and NOTICE files with full attribution to original Home Assistant Cloudflare integration authors

## [1.2.0] - 2026-03-26
### Added
- **Sensor: Last Sync** — timestamp sensor showing when the last sync attempt ran
- **Sensor: Sync Status** — shows "Up to date", "X record(s) updated", "Failed", or "Pending"
- **Button: Sync Now** — press to trigger an immediate DNS update from the HA dashboard
- **Configurable poll interval** — set update frequency (in minutes) via the Configure dialog; minimum 5 minutes with a warning below 15
- All new entities grouped under a single Cloudflare DDNS device card in HA

## [1.1.1] - 2026-03-26
### Fixed
- Skip updating a stale record if another record with the same name in the same zone already holds the target IP, preventing a Cloudflare "duplicate record" API error

## [1.1.0] - 2026-03-26
### Fixed
- Improved exception handling in the update coordinator to catch and report all error types, not just Cloudflare API errors
- Added detailed debug logging for each record update (old IP → new IP) to aid troubleshooting

## [1.0.0] - 2026-03-26
### Added
- Initial release
- Multi-zone support — select any number of authorized Cloudflare zones during setup
- Multi-record support — select any number of DNS `A` records across all selected zones
- Options flow — update zones and records at any time via the Configure button without reinstalling
- Automatic config entry migration from the original single-zone schema
- `cloudflare_ddns.update_records` service for manual trigger from automations
- HACS support via `hacs.json`
