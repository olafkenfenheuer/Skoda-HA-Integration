"""The Škoda Connect integration."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.const import CONF_SCAN_INTERVAL, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import SkodaApi
from .const import (
    CONF_API_KEY,
    CONF_READ_ONLY,
    CONF_VINS,
    DEFAULT_SCAN_INTERVAL_MINUTES,
)
from .coordinator import SkodaConfigEntry, SkodaDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.CLIMATE,
    Platform.DEVICE_TRACKER,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: SkodaConfigEntry) -> bool:
    """Set up Škoda Connect from a config entry."""
    api_key = entry.data.get(CONF_API_KEY)
    vins = entry.data.get(CONF_VINS)
    if not api_key or not vins:
        # Entry created by a version that logged in with email and password: the public
        # API only accepts API keys, so ask the user for one.
        raise ConfigEntryAuthFailed("An API key is required; create one in the MyŠkoda app")

    api = SkodaApi(async_get_clientsession(hass), api_key)
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES)
    coordinator = SkodaDataUpdateCoordinator(
        hass,
        entry,
        api,
        list(vins),
        update_interval=timedelta(minutes=scan_interval),
    )
    coordinator.read_only = entry.options.get(CONF_READ_ONLY, False)

    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: SkodaConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_update_listener(hass: HomeAssistant, entry: SkodaConfigEntry) -> None:
    """Apply changed options; only reload when something other than the interval changed."""
    coordinator = entry.runtime_data
    if entry.options.get(CONF_READ_ONLY, False) == coordinator.read_only:
        minutes = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES)
        coordinator.set_update_interval(timedelta(minutes=minutes))
        return
    await hass.config_entries.async_reload(entry.entry_id)
