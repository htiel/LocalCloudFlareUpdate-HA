# Changelog

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
