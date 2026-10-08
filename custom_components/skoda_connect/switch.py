"""Switch platform for the Škoda Connect integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import SkodaConfigEntry, SkodaDataUpdateCoordinator
from .entity import SkodaVehicleEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SkodaConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Škoda Connect switches from a config entry."""
    coordinator = entry.runtime_data
    async_add_entities(
        SkodaChargingSwitch(coordinator, vin)
        for vin, vehicle in coordinator.data.vehicles.items()
        if vehicle.has("charging", "status") and vehicle.supports("startCharging")
    )


class SkodaChargingSwitch(SkodaVehicleEntity, SwitchEntity):
    """Starts and stops charging."""

    _attr_translation_key = "charging"

    def __init__(self, coordinator: SkodaDataUpdateCoordinator, vin: str) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, vin)
        self._attr_unique_id = f"{vin}_charging"

    @property
    def is_on(self) -> bool | None:
        """Return true if the vehicle is currently charging."""
        state = self.vehicle.get("charging", "status", "state")
        return None if state is None else state == "CHARGING"

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Start charging."""
        await self.coordinator.async_command(
            self.vin, self.coordinator.api.start_charging(self.vin)
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Stop charging."""
        await self.coordinator.async_command(
            self.vin, self.coordinator.api.stop_charging(self.vin)
        )
