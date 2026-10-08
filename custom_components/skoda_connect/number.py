"""Number platform for the Škoda Connect integration."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import SkodaVehicle
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
        SkodaChargeLimitNumber(coordinator, vin)
        for vin, vehicle in coordinator.data.vehicles.items()
        if _has_charge_limit(vehicle)
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
