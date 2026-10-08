"""Data update coordinator for the Škoda Connect integration."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Awaitable
from dataclasses import dataclass, field
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import CALLBACK_TYPE, HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    SkodaApi,
    SkodaApiError,
    SkodaAuthError,
    SkodaRateLimitError,
    SkodaVehicle,
)
from .const import (
    CONF_CHARGING_SCAN_INTERVAL,
    CONF_PLUGGED_IN_FAST_POLLING,
    CONF_VEHICLE_INTERVALS,
    DEFAULT_CHARGING_SCAN_INTERVAL_MINUTES,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DOMAIN,
    POST_COMMAND_REFRESH_DELAY,
)

_LOGGER = logging.getLogger(__name__)

MIN_RATE_LIMIT_BACKOFF = timedelta(minutes=15)
MAX_RATE_LIMIT_BACKOFF = timedelta(hours=1)
# A vehicle counts as due slightly early so scheduler jitter never skips a whole tick.
DUE_TOLERANCE_SECONDS = 10


@dataclass
class SkodaData:
    """Container for all configured vehicles."""

    vehicles: dict[str, SkodaVehicle] = field(default_factory=dict)


class SkodaDataUpdateCoordinator(DataUpdateCoordinator[SkodaData]):
    """Coordinator that polls the MyŠkoda Public API for every configured vehicle."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: SkodaConfigEntry,
        api: SkodaApi,
        vins: list[str],
    ) -> None:
        """Set up the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=None,
        )
        self.api = api
        self.vins = vins
        self.read_only = False
        self._cancel_refresh: CALLBACK_TYPE | None = None
        self._last_fetch: dict[str, float] = {}
        self._force: set[str] = set()
        self.update_interval = self._shortest_interval()

    # -- per-vehicle polling intervals -------------------------------------------------

    def is_charging(self, vin: str) -> bool:
        """Return whether the last known state of the vehicle is "charging"."""
        vehicle = self.data.vehicles.get(vin) if self.data else None
        return bool(vehicle and vehicle.get("charging", "status", "state") == "CHARGING")

    def is_plugged_in(self, vin: str) -> bool:
        """Return whether the last known state says the charging cable is plugged in."""
        vehicle = self.data.vehicles.get(vin) if self.data else None
        if vehicle is None:
            return False
        plug = vehicle.get("charging", "status", "plugConnectionState")
        if plug is not None:
            return plug == "CONNECTED"
        # Older responses lack the plug state; a disconnected plug is always CONNECT_CABLE.
        state = vehicle.get("charging", "status", "state")
        return state is not None and state != "CONNECT_CABLE"

    def uses_charging_interval(self, vin: str) -> bool:
        """Return whether the vehicle is polled at its (shorter) charging interval."""
        if self.is_charging(vin):
            return True
        return bool(
            self.config_entry.options.get(CONF_PLUGGED_IN_FAST_POLLING, False)
            and self.is_plugged_in(vin)
        )

    def interval_minutes(self, vin: str, kind: str) -> int:
        """Return the configured interval of a vehicle; ``kind`` is "idle" or "charging"."""
        options = self.config_entry.options
        override = options.get(CONF_VEHICLE_INTERVALS, {}).get(vin, {}).get(kind)
        if override is not None:
            return int(override)
        if kind == "charging":
            return int(
                options.get(CONF_CHARGING_SCAN_INTERVAL, DEFAULT_CHARGING_SCAN_INTERVAL_MINUTES)
            )
        return int(options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES))

    def _interval_for(self, vin: str) -> timedelta:
        kind = "charging" if self.uses_charging_interval(vin) else "idle"
        return timedelta(minutes=self.interval_minutes(vin, kind))

    def _shortest_interval(self) -> timedelta:
        return min(self._interval_for(vin) for vin in self.vins)

    def _is_due(self, vin: str) -> bool:
        if vin in self._force or not self.data or vin not in self.data.vehicles:
            return True
        elapsed = time.monotonic() - self._last_fetch.get(vin, 0)
        return elapsed >= self._interval_for(vin).total_seconds() - DUE_TOLERANCE_SECONDS

    def reschedule(self) -> None:
        """Apply changed interval settings to the next poll."""
        interval = self._shortest_interval()
        if interval != self.update_interval:
            self.update_interval = interval
            self._schedule_refresh()

    async def _async_update_data(self) -> SkodaData:
        """Fetch the latest data for every vehicle from the cloud API."""
        due = [vin for vin in self.vins if self._is_due(vin)]
        results = await asyncio.gather(
            *(self.api.get_vehicle(vin) for vin in due), return_exceptions=True
        )
        fetched = dict(zip(due, results, strict=True))
        self._force.clear()

        vehicles: dict[str, SkodaVehicle] = {}
        failures: list[Exception] = []
        for vin in self.vins:
            if vin not in fetched:
                # Not due yet: keep the last known state.
                vehicles[vin] = self.data.vehicles[vin]
                continue
            result = fetched[vin]
            if isinstance(result, SkodaAuthError):
                raise ConfigEntryAuthFailed(str(result)) from result
            if isinstance(result, SkodaRateLimitError):
                backoff = self._rate_limit_backoff(result)
                _LOGGER.warning(
                    "Škoda Connect API rate limit hit; pausing polling for %s", backoff
                )
                raise UpdateFailed(
                    "Škoda Connect API rate limit reached; backing off",
                    retry_after=backoff.total_seconds(),
                ) from result
            if isinstance(result, Exception):
                failures.append(result)
                # Keep the last known state for a vehicle whose request failed.
                if self.data and vin in self.data.vehicles:
                    vehicles[vin] = self.data.vehicles[vin]
                continue
            vehicles[vin] = result
            self._last_fetch[vin] = time.monotonic()

        if failures and len(failures) == len(fetched):
            raise UpdateFailed(
                f"Error communicating with Škoda Connect API: {failures[0]}"
            ) from failures[0]
        for failure in failures:
            _LOGGER.warning("Could not update a vehicle: %s", failure)
        data = SkodaData(vehicles=vehicles)
        # A vehicle that started or stopped charging switches to its other interval.
        self.data = data
        self.update_interval = self._shortest_interval()
        return data

    @staticmethod
    def _rate_limit_backoff(err: SkodaRateLimitError) -> timedelta:
        backoff = err.retry_after if err.retry_after is not None else MIN_RATE_LIMIT_BACKOFF
        return min(max(backoff, MIN_RATE_LIMIT_BACKOFF), MAX_RATE_LIMIT_BACKOFF)

    async def async_command(self, vin: str, command: Awaitable[None]) -> None:
        """Run a remote command and schedule a single follow-up refresh of that vehicle.

        Commands count against the same request quota as polling, so instead of
        refreshing after every call this waits a moment for the vehicle and refreshes once.
        """
        if self.read_only:
            command.close()  # type: ignore[attr-defined]
            raise HomeAssistantError(
                "Škoda Connect is configured in read-only mode; disable it in the "
                "integration options to use this control"
            )
        try:
            await command
        except SkodaAuthError as err:
            raise HomeAssistantError(f"The API key was rejected: {err}") from err
        except SkodaRateLimitError as err:
            raise HomeAssistantError(f"Škoda Connect API rate limit reached: {err}") from err
        except SkodaApiError as err:
            raise HomeAssistantError(f"The vehicle did not accept the request: {err}") from err

        self._force.add(vin)
        if self._cancel_refresh:
            self._cancel_refresh()
        self._cancel_refresh = async_call_later(
            self.hass, POST_COMMAND_REFRESH_DELAY, self._async_delayed_refresh
        )

    async def _async_delayed_refresh(self, _now) -> None:
        self._cancel_refresh = None
        await self.async_request_refresh()

    async def async_shutdown(self) -> None:
        """Cancel any pending follow-up refresh."""
        if self._cancel_refresh:
            self._cancel_refresh()
            self._cancel_refresh = None
        await super().async_shutdown()


# Generic alias used to type-annotate config entries for this integration.
SkodaConfigEntry = ConfigEntry[SkodaDataUpdateCoordinator]
