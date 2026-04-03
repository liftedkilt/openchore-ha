"""Sensor platform for OpenChore."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import OpenChoreCoordinator


class OpenChoreSensorBase(CoordinatorEntity[OpenChoreCoordinator], SensorEntity):
    """Base class for OpenChore sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: OpenChoreCoordinator,
        entry_id: str,
        key: str,
        name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_{key}"
        self._attr_name = name

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info for grouping entities."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.base_url)},
            name="OpenChore",
            manufacturer="OpenChore",
            entry_type=DeviceEntryType.SERVICE,
        )


class OpenChoreCountSensor(OpenChoreSensorBase):
    """Sensor showing the total number of triggerable chores."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "chores"
    _attr_icon = "mdi:clipboard-check-multiple-outline"

    def __init__(self, coordinator: OpenChoreCoordinator, entry_id: str) -> None:
        """Initialize the chore count sensor."""
        super().__init__(coordinator, entry_id, "chore_count", "Chore Count")

    @property
    def native_value(self) -> int:
        """Return the number of triggerable chores."""
        if not self.coordinator.data:
            return 0
        return len(self.coordinator.data.chores)

    @property
    def extra_state_attributes(self) -> dict:
        """Return the list of chore titles."""
        if not self.coordinator.data:
            return {"chores": []}
        return {
            "chores": [
                chore.get("title", "Unknown")
                for chore in self.coordinator.data.chores
            ]
        }


class OpenChoreUserCountSensor(OpenChoreSensorBase):
    """Sensor showing the total number of users."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "users"
    _attr_icon = "mdi:account-group"

    def __init__(self, coordinator: OpenChoreCoordinator, entry_id: str) -> None:
        """Initialize the user count sensor."""
        super().__init__(coordinator, entry_id, "user_count", "User Count")

    @property
    def native_value(self) -> int:
        """Return the number of users."""
        if not self.coordinator.data:
            return 0
        return len(self.coordinator.data.users)

    @property
    def extra_state_attributes(self) -> dict:
        """Return the list of user names."""
        if not self.coordinator.data:
            return {"users": []}
        return {
            "users": [
                user.get("name", "Unknown")
                for user in self.coordinator.data.users
            ]
        }


class OpenChorePerChoreSensor(OpenChoreSensorBase):
    """Sensor showing the trigger count for an individual chore."""

    _attr_icon = "mdi:clipboard-check-outline"

    def __init__(
        self,
        coordinator: OpenChoreCoordinator,
        entry_id: str,
        chore: dict,
    ) -> None:
        """Initialize the per-chore sensor."""
        triggers = chore.get("triggers", [])
        first_uuid = triggers[0].get("uuid", "unknown") if triggers else "unknown"
        title = chore.get("title", "Unknown")
        super().__init__(
            coordinator,
            entry_id,
            f"chore_{first_uuid}",
            title,
        )
        self._first_uuid = first_uuid
        self._chore_title = title

    @property
    def native_value(self) -> int:
        """Return the number of triggers for this chore."""
        if not self.coordinator.data:
            return 0
        for chore in self.coordinator.data.chores:
            triggers = chore.get("triggers", [])
            for trigger in triggers:
                if trigger.get("uuid") == self._first_uuid:
                    return len(triggers)
        return 0

    @property
    def extra_state_attributes(self) -> dict:
        """Return trigger UUIDs and title."""
        if not self.coordinator.data:
            return {"trigger_uuids": [], "title": self._chore_title}
        for chore in self.coordinator.data.chores:
            triggers = chore.get("triggers", [])
            for trigger in triggers:
                if trigger.get("uuid") == self._first_uuid:
                    return {
                        "trigger_uuids": [
                            t.get("uuid", "") for t in triggers
                        ],
                        "title": chore.get("title", self._chore_title),
                    }
        return {"trigger_uuids": [], "title": self._chore_title}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up OpenChore sensor entities from a config entry."""
    coordinator: OpenChoreCoordinator = entry.runtime_data
    entities: list[SensorEntity] = [
        OpenChoreCountSensor(coordinator, entry.entry_id),
        OpenChoreUserCountSensor(coordinator, entry.entry_id),
    ]
    if coordinator.data:
        for chore in coordinator.data.chores:
            entities.append(
                OpenChorePerChoreSensor(coordinator, entry.entry_id, chore)
            )
    async_add_entities(entities)
