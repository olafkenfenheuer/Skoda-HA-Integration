"""Sensor platform for the Škoda Connect integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    UnitOfLength,
    UnitOfPower,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .api import SkodaVehicle as Vehicle
from .coordinator import POLL_STATUSES, PollResult, SkodaConfigEntry, SkodaDataUpdateCoordinator
from .entity import SkodaVehicleEntity


@dataclass(frozen=True, kw_only=True)
class SkodaSensorEntityDescription(SensorEntityDescription):
    """Describes a Škoda Connect sensor entity."""

    value_fn: Callable[[Vehicle], StateType]
    exists_fn: Callable[[Vehicle], bool] = lambda vehicle: True


def _battery_percent(vehicle: Vehicle) -> StateType:
    value = vehicle.get("charging", "status", "battery", "stateOfChargeInPercent")
    if value is None:
        for engine in ("primaryEngineRange", "secondaryEngineRange"):
            if vehicle.get("fuelStatus", engine, "engineType") == "ELECTRIC":
                return vehicle.get("fuelStatus", engine, "currentSoCInPercent")
    return value


def _battery_range_km(vehicle: Vehicle) -> StateType:
    meters = vehicle.get("charging", "status", "battery", "remainingCruisingRangeInMeters")
    return None if meters is None else round(meters / 1000)


def _fuel_level(vehicle: Vehicle) -> StateType:
    for engine in ("primaryEngineRange", "secondaryEngineRange"):
        value = vehicle.get("fuelStatus", engine, "currentFuelLevelInPercent")
        if value is not None:
            return value
    return None


def _path(*path: str) -> Callable[[Vehicle], StateType]:
    return lambda vehicle: vehicle.get(*path)


def _exists(*path: str) -> Callable[[Vehicle], bool]:
    return lambda vehicle: vehicle.has(*path)


def _charging_location_profile(vehicle: Vehicle) -> StateType:
    """Return the name of the saved charging location the vehicle is currently at.

    Only meaningful while the vehicle is actually at a saved location -
    ``currentVehiclePositionProfile`` can otherwise still carry a stale name.
    """
    if not vehicle.get("charging", "isVehicleInSavedLocation"):
        return None
    return vehicle.get("chargingProfiles", "currentVehiclePositionProfile", "name")


SENSOR_DESCRIPTIONS: tuple[SkodaSensorEntityDescription, ...] = (
    SkodaSensorEntityDescription(
        key="battery_level",
        translation_key="battery_level",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=_battery_percent,
        exists_fn=lambda v: _battery_percent(v) is not None,
    ),
    SkodaSensorEntityDescription(
        key="charge_power",
        translation_key="charge_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        value_fn=_path("charging", "status", "chargePowerInKw"),
        exists_fn=_exists("charging", "status"),
    ),
    SkodaSensorEntityDescription(
        key="charging_rate",
        translation_key="charging_rate",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        value_fn=_path("charging", "status", "chargingRateInKilometersPerHour"),
        exists_fn=_exists("charging", "status"),
    ),
    SkodaSensorEntityDescription(
        key="remaining_charging_time",
        translation_key="remaining_charging_time",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement="min",
        value_fn=_path("charging", "status", "remainingTimeToFullyChargedInMinutes"),
        exists_fn=_exists("charging", "status"),
    ),
    SkodaSensorEntityDescription(
        key="battery_range",
        translation_key="battery_range",
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        value_fn=_battery_range_km,
        exists_fn=lambda v: _battery_range_km(v) is not None,
    ),
    SkodaSensorEntityDescription(
        key="total_range",
        translation_key="total_range",
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        value_fn=_path("fuelStatus", "totalRangeInKm"),
        exists_fn=_exists("fuelStatus", "totalRangeInKm"),
    ),
    SkodaSensorEntityDescription(
        key="fuel_level",
        translation_key="fuel_level",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=_fuel_level,
        exists_fn=lambda v: _fuel_level(v) is not None,
    ),
    SkodaSensorEntityDescription(
        key="ad_blue_range",
        translation_key="ad_blue_range",
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        value_fn=_path("fuelStatus", "adBlueRange"),
        exists_fn=_exists("fuelStatus", "adBlueRange"),
    ),
    SkodaSensorEntityDescription(
        key="mileage",
        translation_key="mileage",
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        value_fn=_path("odometer", "mileageInKm"),
        exists_fn=_exists("odometer", "mileageInKm"),
    ),
    SkodaSensorEntityDescription(
        key="target_temperature",
        translation_key="target_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_registry_enabled_default=False,
        value_fn=_path("airConditioning", "targetTemperature", "value"),
        exists_fn=_exists("airConditioning", "targetTemperature", "value"),
    ),
    SkodaSensorEntityDescription(
        key="location_address",
        translation_key="location_address",
        icon="mdi:map-marker",
        value_fn=_path("parkingPosition", "formattedAddress"),
        exists_fn=_exists("parkingPosition", "formattedAddress"),
    ),
    SkodaSensorEntityDescription(
        key="charging_location_profile",
        translation_key="charging_location_profile",
        icon="mdi:map-marker-radius",
        value_fn=_charging_location_profile,
        exists_fn=_exists("chargingProfiles"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SkodaConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Škoda Connect sensors from a config entry."""
    coordinator = entry.runtime_data
    entities: list[SkodaSensor] = []
    for vin, vehicle in coordinator.data.vehicles.items():
        for description in SENSOR_DESCRIPTIONS:
            if description.exists_fn(vehicle):
                entities.append(SkodaSensor(coordinator, vin, description))
        entities.append(SkodaApiStatusSensor(coordinator, vin))
    async_add_entities(entities)


class SkodaSensor(SkodaVehicleEntity, SensorEntity):
    """Represents a single data point of a Škoda vehicle."""

    entity_description: SkodaSensorEntityDescription

    def __init__(
        self,
        coordinator: SkodaDataUpdateCoordinator,
        vin: str,
        description: SkodaSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, vin)
        self.entity_description = description
        self._attr_unique_id = f"{vin}_{description.key}"

    @property
    def native_value(self) -> StateType:
        """Return the current value, tolerating missing upstream data."""
        try:
            return self.entity_description.value_fn(self.vehicle)
        except (KeyError, TypeError):
            return None


class SkodaApiStatusSensor(SkodaVehicleEntity, SensorEntity):
    """Shows the result of the last API request that polled the vehicle."""

    _attr_translation_key = "api_status"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = POLL_STATUSES
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: SkodaDataUpdateCoordinator, vin: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, vin)
        self._attr_unique_id = f"{vin}_api_status"

    @property
    def available(self) -> bool:
        """Stay available while polling fails - that is when the status matters most."""
        return True

    @property
    def _result(self) -> PollResult | None:
        return self.coordinator.poll_results.get(self.vin)

    @property
    def native_value(self) -> str | None:
        """Return the outcome of the last poll."""
        result = self._result
        return result.status if result else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return when the last poll happened and what went wrong, if anything."""
        attributes: dict[str, Any] = {}
        if (last_success := self.coordinator.last_success.get(self.vin)) is not None:
            attributes["last_success"] = last_success
        if (result := self._result) is None:
            return attributes
        attributes["last_poll"] = result.time
        if result.error:
            attributes["error"] = result.error
        if result.http_status is not None:
            attributes["http_status"] = result.http_status
        if result.problem:
            attributes["problem"] = result.problem
        if result.omitted:
            attributes["omitted_parts"] = result.omitted
        return attributes
