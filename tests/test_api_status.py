"""Tests for the API status diagnostic sensor."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.skoda_connect.api import (
    SkodaApiError,
    SkodaAuthError,
    SkodaRateLimitError,
)

from .conftest import VIN, make_vehicle

GET = "custom_components.skoda_connect.api.SkodaApi.get_vehicle"


def _status_id(hass: HomeAssistant) -> str:
    return er.async_get(hass).async_get_entity_id("sensor", "skoda_connect", f"{VIN}_api_status")


async def test_status_ok(hass: HomeAssistant, mock_entry: MockConfigEntry, mock_get_vehicle):
    mock_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()
    state = hass.states.get(_status_id(hass))
    assert state.state == "ok"
    assert state.attributes["last_success"] == state.attributes["last_poll"]


async def test_status_partial(hass: HomeAssistant, mock_entry: MockConfigEntry):
    vehicle = make_vehicle()
    vehicle.errors = ["parkingPosition"]
    mock_entry.add_to_hass(hass)
    with patch(GET, new=AsyncMock(return_value=vehicle)):
        await hass.config_entries.async_setup(mock_entry.entry_id)
        await hass.async_block_till_done()
    state = hass.states.get(_status_id(hass))
    assert state.state == "partial"
    assert state.attributes["omitted_parts"] == ["parkingPosition"]


async def test_status_after_failure_stays_available(
    hass: HomeAssistant, mock_entry: MockConfigEntry, mock_get_vehicle
):
    mock_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()
    coordinator = mock_entry.runtime_data

    err = SkodaApiError("boom", status=500, problem="internal-error")
    mock_get_vehicle.side_effect = err
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    state = hass.states.get(_status_id(hass))
    assert state.state == "api_error"
    assert state.attributes["http_status"] == 500
    assert state.attributes["problem"] == "internal-error"
    assert state.attributes["error"] == "boom"
    assert "last_success" in state.attributes

    mock_get_vehicle.side_effect = SkodaRateLimitError("slow down", status=429)
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(_status_id(hass)).state == "rate_limited"

    mock_get_vehicle.side_effect = SkodaAuthError("expired", status=401, problem="api-key-expired")
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(_status_id(hass)).state == "auth_error"
