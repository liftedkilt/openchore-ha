"""The OpenChore integration."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv

from .const import (
    ATTR_ASSIGN_TO,
    ATTR_AVAILABLE_AT,
    ATTR_DUE_BY,
    ATTR_TRIGGER_UUID,
    CONF_TOKEN,
    CONF_URL,
    DOMAIN,
    SERVICE_TRIGGER_CHORE,
)
from .coordinator import OpenChoreCoordinator

_LOGGER = logging.getLogger(__name__)

OpenChoreConfigEntry = ConfigEntry[OpenChoreCoordinator]

TRIGGER_CHORE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_TRIGGER_UUID): cv.string,
        vol.Optional(ATTR_ASSIGN_TO): cv.string,
        vol.Optional(ATTR_DUE_BY): cv.string,
        vol.Optional(ATTR_AVAILABLE_AT): cv.string,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: OpenChoreConfigEntry) -> bool:
    """Set up OpenChore from a config entry."""
    url = entry.data[CONF_URL]
    token = entry.data[CONF_TOKEN]

    coordinator = OpenChoreCoordinator(hass, url, token)

    # Perform initial data fetch; raises ConfigEntryNotReady on failure
    await coordinator.async_config_entry_first_refresh()

    # Store the coordinator on the entry's runtime_data
    entry.runtime_data = coordinator

    # Register service (only once, even with multiple config entries)
    if not hass.services.has_service(DOMAIN, SERVICE_TRIGGER_CHORE):
        _register_services(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: OpenChoreConfigEntry) -> bool:
    """Unload a config entry."""
    # If this was the last entry, remove our services
    remaining = [
        e
        for e in hass.config_entries.async_entries(DOMAIN)
        if e.entry_id != entry.entry_id
    ]
    if not remaining:
        hass.services.async_remove(DOMAIN, SERVICE_TRIGGER_CHORE)

    return True


def _get_coordinator(hass: HomeAssistant) -> OpenChoreCoordinator:
    """Get the first available coordinator (for service calls)."""
    entries = hass.config_entries.async_entries(DOMAIN)
    for entry in entries:
        if hasattr(entry, "runtime_data") and entry.runtime_data is not None:
            return entry.runtime_data
    raise HomeAssistantError("No active OpenChore integration found")


def _register_services(hass: HomeAssistant) -> None:
    """Register the openchore.trigger_chore service."""

    async def handle_trigger_chore(call: ServiceCall) -> None:
        """Handle the trigger_chore service call."""
        coordinator = _get_coordinator(hass)

        trigger_uuid: str = call.data[ATTR_TRIGGER_UUID]
        assign_to: str | None = call.data.get(ATTR_ASSIGN_TO)
        due_by: str | None = call.data.get(ATTR_DUE_BY)
        available_at: str | None = call.data.get(ATTR_AVAILABLE_AT)

        # Validate trigger UUID against known data (if coordinator has data)
        if coordinator.data and not coordinator.data.trigger_uuid_valid(trigger_uuid):
            raise ServiceValidationError(
                f"Unknown trigger UUID: {trigger_uuid}. "
                "Check the OpenChore admin panel for valid trigger UUIDs."
            )

        # Validate username if provided
        if assign_to and coordinator.data and not coordinator.data.user_name_valid(assign_to):
            raise ServiceValidationError(
                f"Unknown user: {assign_to}. "
                "Valid users: "
                + ", ".join(u.get("name", "") for u in coordinator.data.users)
            )

        try:
            result = await coordinator.async_trigger_chore(
                trigger_uuid=trigger_uuid,
                assign_to=assign_to,
                due_by=due_by,
                available_at=available_at,
            )
            _LOGGER.info(
                "Chore triggered: %s assigned to %s (schedule %s)",
                result.get("chore"),
                result.get("assigned_to"),
                result.get("schedule_id"),
            )
        except Exception as err:
            raise HomeAssistantError(f"Failed to trigger chore: {err}") from err

    hass.services.async_register(
        DOMAIN,
        SERVICE_TRIGGER_CHORE,
        handle_trigger_chore,
        schema=TRIGGER_CHORE_SCHEMA,
    )
