"""Number platform for the Škoda Connect integration."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import CONF_SCAN_INTERVAL, PERCENTAGE, EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import SkodaVehicle
from .const import (
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DOMAIN,
    MANUFACTURER,
    MIN_SCAN_INTERVAL_MINUTES,
    POLL_INTERVAL_NUMBER_MAX_MINUTES,
)
from .coordinator import SkodaConfigEntry, SkodaDataUpdateCoordinator
from .entity import SkodaVehicleEntity


def _has_charge_limit(vehicle: SkodaVehicle) -> bool:
    return vehicle.has("charging", "settings", "targetStateOfChargeInPercent")


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SkodaConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Škoda Connect charge limit number entity from a config entry."""
    coordinator = entry.runtime_data
    async_add_entities(
        [
            SkodaChargeLimitNumber(coordinator, vin)
            for vin, vehicle in coordinator.data.vehicles.items()
            if _has_charge_limit(vehicle)
        ]
        + [SkodaPollIntervalNumber(entry, coordinator)]
    )


class SkodaChargeLimitNumber(SkodaVehicleEntity, NumberEntity):
    """Represents the target state-of-charge limit."""

    _attr_translation_key = "charge_limit"
    _attr_native_unit_of_measurement = PERCENTAGE
    # Vehicles typically accept 50-100 in steps of 10 and reject other values.
    _attr_native_min_value = 50
    _attr_native_max_value = 100
    _attr_native_step = 10
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator: SkodaDataUpdateCoordinator, vin: str) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator, vin)
        self._attr_unique_id = f"{vin}_charge_limit"

    @property
    def native_value(self) -> float | None:
        """Return the currently configured charge limit."""
        return self.vehicle.get("charging", "settings", "targetStateOfChargeInPercent")

    async def async_set_native_value(self, value: float) -> None:
        """Set a new charge limit."""
        await self.coordinator.async_command(
            self.coordinator.api.set_charging_limit(self.vin, int(value))
        )


class SkodaPollIntervalNumber(CoordinatorEntity[SkodaDataUpdateCoordinator], NumberEntity):
    """Controls how often the cloud API is polled (applies immediately, no reload)."""

    _attr_has_entity_name = True
    _attr_translation_key = "poll_interval"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_native_min_value = MIN_SCAN_INTERVAL_MINUTES
    _attr_native_max_value = POLL_INTERVAL_NUMBER_MAX_MINUTES
    _attr_native_step = 5
    _attr_mode = NumberMode.SLIDER

    def __init__(self, entry, coordinator: SkodaDataUpdateCoordinator) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_poll_interval"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer=MANUFACTURER,
            name="Škoda Connect",
        )

    @property
    def native_value(self) -> float:
        """Return the current polling interval in minutes."""
        return self._entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES)

    async def async_set_native_value(self, value: float) -> None:
        """Persist and apply a new polling interval."""
        minutes = int(value)
        # The entry's update listener applies the new interval without reloading.
        self.hass.config_entries.async_update_entry(
            self._entry, options={**self._entry.options, CONF_SCAN_INTERVAL: minutes}
        )
        self.async_write_ha_state()
