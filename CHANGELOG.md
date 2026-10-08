# Changelog

[🇬🇧 English](CHANGELOG.md) | [🇳🇱 Nederlands](CHANGELOG.nl.md)

All notable changes to this integration are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.3.5]

### Added

- Per-vehicle switch "Charging interval while plugged in" (configuration category). It overrides the
  global option of the same name for that vehicle and applies immediately.

## [0.3.4]

### Added

- New option "Use the charging interval while the cable is plugged in" (off by default): a vehicle
  with a plugged-in charging cable is polled at its charging interval even when it is not charging
  yet, e.g. to catch the start of a timer-controlled charge quickly.

## [0.3.3]

### Added

- **Reconfigure flow**: a new API key (and the VIN list) can be entered at any time via
  *Reconfigure* on the integration entry, e.g. before the current key expires. The key is validated
  first; entities, history and options are kept.

## [0.3.2]

### Added

- Škoda icon for the integration, shipped as `brand/icon.png` (shown by Home Assistant 2026.3 or newer).

## [0.3.1]

### Added

- **Per-vehicle polling intervals**: each vehicle gets `number` entities "Polling interval" and
  "Polling interval while charging" (5-120 min). A vehicle is polled at its shorter charging
  interval while it is charging. Changes apply immediately without a reload and are stored in the
  entry options. New option "Polling interval while charging" (default 5 min) sets the default.
- A command now refreshes only the vehicle it was sent to.

## [0.3.0]

### Changed

- **Migrated to the official MyŠkoda Public API**
  (<https://public.api.connect.skoda-auto.cz/docs>). Authentication now uses an API key created
  in the MyŠkoda app instead of email and password, and the `myskoda` Python dependency was
  removed. Existing entries ask for reauthentication to enter an API key and the VIN(s).
- Polling now costs one request per vehicle (was 10-13). Default interval is 10 minutes
  (minimum 5) because the API allows 20 requests per hour and VIN.
- Remote commands no longer trigger an immediate refresh; one refresh follows 30 seconds
  after the last command.
- The vehicle lock is now a read-only `binary_sensor` (`unlocked`).

### Added

- `select` entity for the charge mode.
- Diagnostics redact the API key, VINs, license plate, position and address.

### Removed

- Features without a public API endpoint: lock/unlock (and the S-PIN option), honk & flash,
  flash, wake up, window heating switch, battery care mode switch, reduced charging current
  switch, outside temperature and software version sensors.

## [0.2.0]

### Added

- **Charging location sensors**: a new `sensor.charging_location_profile` shows the name of
  the saved charging location (e.g. "Home") the vehicle is currently matched to, and
  `binary_sensor.vehicle_in_saved_location` reports whether the vehicle is at a saved charging
  location at all. The sensor's value is tied to the binary sensor so it can't keep showing a
  stale location name after the vehicle has driven away.
- **Location address sensor**: `sensor.location_address` shows a human-readable address for
  the vehicle's last known position, built from the live position's address or, if that isn't
  available, the last known parking position — a plain-text complement to the existing
  `device_tracker.vehicle_location`, which continues to be the entity that puts the vehicle on
  the Map dashboard.
- **Rate limit handling**: the coordinator now explicitly detects HTTP 429/430 responses from
  the Škoda Connect API, honors the `Retry-After` header (falling back to a bounded 15
  minute–1 hour pause when it's absent), and backs off for exactly one cycle via Home
  Assistant's native retry mechanism instead of hammering the API again immediately. The same
  condition is now shown as a dedicated, translated "rate limited" error during login and
  reauthentication.

### Changed

- Lowered the minimum configurable polling interval from 1 minute to 15 minutes, and the
  default from 30 to 15 minutes. Fetching one vehicle's full state costs roughly 10–13 separate
  API requests, and the API enforces a strict per-account quota — a 1-minute interval
  made it trivially easy to get rate limited or even locked out. See the "Notes on the API"
  section in the README for more detail if you have several vehicles on one account.

## [0.1.0] - 2026-08-28

Initial release: a Home Assistant integration for Škoda vehicles built on the MySkoda app
API, via the [`myskoda`](https://github.com/skodaconnect/myskoda) Python client.

### Added

- UI-only config flow (email/password + optional S-PIN) with reauthentication support, and an
  options flow for the polling interval and a read-only mode.
- `sensor`: battery level, charging power, charging rate, remaining charging time,
  battery/total range, fuel level, AdBlue range, mileage, outside/target temperature, software
  version.
- `binary_sensor`: doors, windows, trunk, bonnet, lights, charging, charging cable plugged in.
- `lock`: central locking (requires S-PIN).
- `device_tracker`: last known vehicle GPS position.
- `climate`: remote air conditioning (on/off, ventilation, target temperature).
- `switch`: window heating, charging, battery care mode, reduced charging current.
- `button`: honk & flash, flash lights, wake up vehicle.
- `number`: AC charge limit.
- Diagnostics download with sensitive data redacted.
- Translations for the config flow, options flow, and entity names in English, Nederlands,
  Deutsch, Français, Čeština and Slovenčina.
