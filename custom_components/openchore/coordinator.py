"""DataUpdateCoordinator for OpenChore."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class OpenChoreData:
    """Parsed data from the OpenChore discovery endpoint."""

    def __init__(self, raw: dict[str, Any]) -> None:
        self.raw = raw
        self.chores: list[dict[str, Any]] = raw.get("chores", [])
        self.users: list[dict[str, Any]] = raw.get("users", [])

    @property
    def trigger_options(self) -> list[dict[str, str]]:
        """Build a flat list of trigger options: {label, value (uuid)}."""
        options: list[dict[str, str]] = []
        for chore in self.chores:
            title = chore.get("title", "Unknown")
            for trigger in chore.get("triggers", []):
                uuid = trigger.get("uuid", "")
                label = f"{title} ({uuid[:8]}...)"
                options.append({"label": label, "value": uuid})
        return options

    @property
    def user_options(self) -> list[dict[str, str]]:
        """Build a list of user options: {label, value (name)}."""
        return [
            {"label": u.get("name", ""), "value": u.get("name", "")}
            for u in self.users
            if u.get("name")
        ]

    def trigger_uuid_valid(self, uuid: str) -> bool:
        """Check whether a trigger UUID exists in the current data."""
        for chore in self.chores:
            for trigger in chore.get("triggers", []):
                if trigger.get("uuid") == uuid:
                    return True
        return False

    def user_name_valid(self, name: str) -> bool:
        """Check whether a username exists in the current data."""
        return any(u.get("name") == name for u in self.users)


class OpenChoreCoordinator(DataUpdateCoordinator[OpenChoreData]):
    """Coordinator that polls the OpenChore discovery endpoint."""

    def __init__(
        self,
        hass: HomeAssistant,
        url: str,
        token: str,
    ) -> None:
        self._url = url.rstrip("/")
        self._token = token

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    @property
    def base_url(self) -> str:
        """Return the configured base URL."""
        return self._url

    @property
    def token(self) -> str:
        """Return the configured API token."""
        return self._token

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json",
        }

    async def _async_update_data(self) -> OpenChoreData:
        """Fetch triggerable chores from the OpenChore server."""
        endpoint = f"{self._url}/api/chores/triggerable"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    endpoint, headers=self._headers(), timeout=aiohttp.ClientTimeout(total=15)
                ) as resp:
                    if resp.status == 401:
                        raise UpdateFailed("Authentication failed (401)")
                    if resp.status == 403:
                        raise UpdateFailed("Forbidden (403) - check API token permissions")
                    resp.raise_for_status()
                    data = await resp.json()
                    return OpenChoreData(data)
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with OpenChore: {err}") from err

    async def async_trigger_chore(
        self,
        trigger_uuid: str,
        assign_to: str | None = None,
        due_by: str | None = None,
        available_at: str | None = None,
    ) -> dict[str, Any]:
        """Fire a chore trigger via the OpenChore webhook endpoint."""
        endpoint = f"{self._url}/api/hooks/trigger/{trigger_uuid}"
        params: dict[str, str] = {}
        if assign_to:
            params["assign_to"] = assign_to
        if due_by:
            params["due_by"] = due_by
        if available_at:
            params["available_at"] = available_at

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    endpoint,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    body = await resp.json()
                    if resp.status == 201:
                        return body
                    # Surface the server error message
                    error_msg = body.get("error", f"HTTP {resp.status}")
                    raise UpdateFailed(f"Trigger failed: {error_msg}")
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with OpenChore: {err}") from err
