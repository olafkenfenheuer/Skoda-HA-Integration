# Škoda Connect for Home Assistant

[🇬🇧 English](README.md) | [🇳🇱 Nederlands](README.nl.md)

A multi-language [Home Assistant](https://www.home-assistant.io/) custom integration for
Škoda vehicles, built on the MySkoda app API via the
actively maintained [`myskoda`](https://github.com/skodaconnect/myskoda) Python client.

> **Unofficial project.** This integration is not affiliated with, endorsed by, or associated
> with Škoda Auto. It uses the same (undocumented) backend API as the official MySkoda app. Use at your own risk.

## Features

Built following Home Assistant's current integration best practices: a UI-only config flow,
a `DataUpdateCoordinator` for efficient polling, entity descriptions, per-entity translations,
an options flow, reauthentication support, and a diagnostics download.

| Platform | Entities |
|---|---|
| `sensor` | Battery level, charging power, charging rate, remaining charging time, battery/total range, fuel level, AdBlue range, mileage, outside/target temperature, software version, address of the vehicle's last known location, name of the charging location profile currently active |
| `binary_sensor` | Doors, windows, trunk, bonnet, lights, charging, charging cable plugged in, vehicle at saved charging location |
| `lock` | Central locking (requires S-PIN) |
| `device_tracker` | Last known vehicle GPS position (shows on the Map dashboard) |
| `climate` | Remote air conditioning (on/off, ventilation, target temperature) |
| `switch` | Window heating, charging, battery care mode, reduced charging current |
| `button` | Honk & flash, flash lights, wake up vehicle |
| `number` | AC charge limit (state of charge) |

Sensors and controls are only created for the data your specific vehicle actually reports, so
the entity list automatically adapts to your car's capabilities (EV, PHEV, or combustion).

A **read-only mode** can be enabled in the integration options to disable all remote controls
(locking, climate, charging, buttons) while keeping all sensors active.

## Supported languages

The integration ships translations for its config flow, options flow, and entity names in:

- English (`en`)
- Nederlands (`nl`)
- Deutsch (`de`)
- Français (`fr`)
- Čeština (`cs`)
- Slovenčina (`sk`)

Home Assistant automatically picks the translation matching your instance's language setting,
falling back to English. Contributions for additional languages are welcome — add a new file
under `custom_components/skoda_connect/translations/`.

This documentation itself is available in [English](README.md) and
[Nederlands](README.nl.md).

## Installation

### HACS (recommended)

1. In HACS, go to **Integrations** → menu (⋮) → **Custom repositories**.
2. Add this repository URL (`https://github.com/max1weber/Skoda-HA-Integration`) with
   category **Integration**.
3. Search for "Škoda Connect" in HACS, click **Download**, and install it.
4. Restart Home Assistant.

### Manual

1. Download or clone this repository.
2. Copy the `custom_components/skoda_connect` folder into your Home Assistant
   `config/custom_components/` directory, so you end up with
   `config/custom_components/skoda_connect/manifest.json`.
3. Restart Home Assistant.

## Configuration

1. Go to **Settings → Devices & Services → Add Integration** and search for "Škoda Connect".
2. Enter the email address and password you use for the MySkoda app.
3. Optionally enter your S-PIN — this is required for the lock entity to work.
4. Home Assistant will validate the login and, on success, create one device per vehicle on
   the account with all applicable entities.
5. After setup, open the integration's **Configure** dialog to change the polling interval
   (15–1440 minutes, default 15) or enable read-only mode.

If your session expires, Home Assistant shows a "reauthenticate" notification — click it and
re-enter your password to restore the connection without losing entity history.

## Notes on the API

This integration deliberately depends on the community-maintained `myskoda` PyPI package rather
than re-implementing the Škoda OAuth2/REST/MQTT client from scratch, so it benefits from
upstream fixes and coverage of the API's evolving vehicle capabilities. Data is refreshed
by polling only — MQTT push notifications from the API are not used, keeping the integration
simple and avoiding an extra point of failure.

### Official public API (not used yet)

Škoda now also offers an official
[MySkoda Public API](https://public.api.connect.skoda-auto.cz/docs) for third-party developers
(authentication via an `X-API-Key` header, keys created in the MySkoda app, bound to selected
vehicles and expiring). **This integration does not use it.** `myskoda` talks to the
app backend (`mysmob.api.connect.skoda-auto.cz`) and logs in with e-mail/password via
`identity.vwgroup.io`. Migrating would need a new client and a different config flow (API key
instead of credentials).

### Rate limits

The MySkoda API enforces a per-account request quota and returns HTTP 429 (Too Many
Requests) once it is exceeded — the `myskoda` client itself does not retry or back off on this.
Community reports (see
[skodaconnect/homeassistant-myskoda#1053](https://github.com/skodaconnect/homeassistant-myskoda/issues/1053))
show that polling too aggressively can get an account temporarily rate limited, or in the worst
case locked out, especially since fetching one vehicle's full state costs roughly 10–13 separate
API requests (one per supported capability, plus vehicle info and maintenance data).

To stay well within the quota, this integration:

- Defaults to a 15-minute polling interval, which is also the enforced minimum in the options
  flow — you cannot accidentally configure a shorter, even riskier interval. If you have
  multiple vehicles on one account, consider raising this.
- Explicitly detects HTTP 429/430 responses and pauses polling, honoring the API's `Retry-After`
  header when present (falling back to a 15-minute pause, capped at 1 hour, if it's absent or
  unparsable), instead of hammering the API again on the very next tick.
- Logs a clear warning when this happens, so you can see it in **Settings → System → Logs**
  rather than the integration silently retrying too soon.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for release notes.

## Disclaimer

Provided as-is, without warranty. Škoda Auto may change its API at any time, which can break
this integration. Use of the MySkoda API is subject to Škoda's own terms of service.
