"""Base entity for the Škoda Connect integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import SkodaVehicle
from .const import DOMAIN, MANUFACTURER
from .coordinator import SkodaDataUpdateCoordinator


class SkodaVehicleEntity(CoordinatorEntity[SkodaDataUpdateCoordinator]):
    """Base class for all entities tied to a single Škoda vehicle."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: SkodaDataUpdateCoordinator, vin: str) -> None:
        """Initialize the entity for a given vehicle VIN."""
        super().__init__(coordinator)
        self.vin = vin
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, vin)},
            manufacturer=MANUFACTURER,
            name=self.vehicle.name,
            serial_number=vin,
        )

    @property
    def vehicle(self) -> SkodaVehicle:
        """Return the current vehicle data from the coordinator."""
        return self.coordinator.data.vehicles[self.vin]

    @property
    def available(self) -> bool:
        """Return True if the coordinator succeeded and this vehicle is present."""
        return super().available and self.vin in self.coordinator.data.vehicles
