# Škoda Connect for Home Assistant

[🇬🇧 English](README.md) | [🇳🇱 Nederlands](README.nl.md)

A multi-language [Home Assistant](https://www.home-assistant.io/) custom integration for
Škoda vehicles, built on the official
[MyŠkoda Public API](https://public.api.connect.skoda-auto.cz/docs). It talks to the API
directly with an **API key** - no username/password and no third-party client library.

> **Unofficial project.** This integration is not affiliated with, endorsed by, or associated
> with Škoda Auto. Use at your own risk.

## Features

Built following Home Assistant's current integration best practices: a UI-only config flow,
a `DataUpdateCoordinator` for efficient polling, entity descriptions, per-entity translations,
an options flow, reauthentication support, and a diagnostics download.

| Platform | Entities |
|---|---|
| `sensor` | Battery level, charging power, charging rate, remaining charging time, battery/total range, fuel level, AdBlue range, mileage, target temperature, address of the parking position, name of the charging location profile currently active |
| `binary_sensor` | Doors, windows, trunk, bonnet, lights, central locking, charging, charging cable plugged in, vehicle at saved charging location |
| `device_tracker` | Parking position (shows on the Map dashboard; unknown while driving) |
| `climate` | Remote air conditioning (on/off, active ventilation, target temperature) |
| `switch` | Start/stop charging |
| `number` | Charge limit (target state of charge), polling interval (5-120 min, applies immediately) |
| `select` | Charge mode |

Sensors and controls are only created for the data and remote operations your specific vehicle
reports, so the entity list adapts to your car (EV, PHEV, or combustion).

A **read-only mode** can be enabled in the integration options to disable all remote controls
while keeping all sensors active.

### What the public API does not offer

Compared to earlier versions (which used the app's private API) the following are no longer
possible, because the public API has no endpoint for them: locking/unlocking, honk & flash,
waking up the vehicle, window heating, battery care mode, reduced charging current, outside
temperature and software version. The lock is now a read-only `binary_sensor`; the other
entities were removed.

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

1. In the MyŠkoda app, create an API key at <https://go.skoda.eu/api-keys> and select the
   vehicle(s) it should be valid for. Keys are bound to those vehicles and expire.
2. Go to **Settings → Devices & Services → Add Integration** and search for "Škoda Connect".
3. Enter the API key and the VIN of each vehicle (several VINs separated by commas). The API
   has no vehicle list endpoint, so the VINs have to be entered manually.
4. Home Assistant validates the key and creates one device per vehicle with all applicable
   entities.
5. After setup, open the integration's **Configure** dialog to change the polling interval
   (5-1440 minutes, default 10) or enable read-only mode.

When the key expires (the API reports `api-key-expired`) Home Assistant shows a
"reauthenticate" notification - create a new key and enter it to restore the connection
without losing entity history.

### Upgrading from 0.2.x

Existing entries used your MySkoda email and password, which the public API does not accept.
After updating, Home Assistant asks you to reauthenticate: enter a new API key and the VIN(s).
Entity IDs and history of the entities that still exist are preserved.

## Notes on the API

The integration only uses the documented endpoints under
`https://public.api.connect.skoda-auto.cz/api/v1/vehicles/{vin}` and authenticates with the
`X-API-Key` header. Data is refreshed by polling.

### Rate limits

The API currently allows **20 requests per hour per VIN** (documented as not final). A poll
costs one request per vehicle, and every remote command costs one more. Therefore this
integration:

- Defaults to a 10-minute polling interval (6 requests/hour) with a 5-minute minimum.
- Does not refresh after every command; commands are accepted asynchronously (HTTP 202), so
  it schedules a single refresh 30 seconds after the last command.
- Detects HTTP 429 responses and pauses polling, honoring `Retry-After` (at least 15 minutes,
  at most 1 hour), and logs a warning when this happens.
- Keeps the last known state of a vehicle if only its request failed.

Parts of the vehicle the API cannot report (for example because the vehicle is asleep) are
simply omitted from its response; the corresponding entities are created once the data is
available, which can require reloading the integration.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for release notes.

## Disclaimer

Provided as-is, without warranty. Škoda Auto may change its API at any time, which can break
this integration. Use of the MyŠkoda Public API is subject to Škoda's own terms of service.
