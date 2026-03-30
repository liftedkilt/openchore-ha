"""Config flow for OpenChore integration."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from .const import CONF_TOKEN, CONF_URL, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_URL): str,
        vol.Required(CONF_TOKEN): str,
    }
)


async def _validate_connection(url: str, token: str) -> dict[str, str] | None:
    """Validate the user input by calling the discovery endpoint.

    Returns None on success, or a dict with an "error" key on failure.
    """
    endpoint = f"{url.rstrip('/')}/api/chores/triggerable"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                endpoint, headers=headers, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 401:
                    return {"error": "invalid_auth"}
                if resp.status == 403:
                    return {"error": "invalid_auth"}
                if resp.status >= 400:
                    return {"error": "cannot_connect"}
                return None
    except (aiohttp.ClientError, TimeoutError):
        return {"error": "cannot_connect"}
    except Exception:  # noqa: BLE001
        _LOGGER.exception("Unexpected error during OpenChore validation")
        return {"error": "unknown"}


class OpenChoreConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for OpenChore."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            url = user_input[CONF_URL].rstrip("/")
            token = user_input[CONF_TOKEN]

            # Prevent duplicate entries for the same server
            await self.async_set_unique_id(url)
            self._abort_if_unique_id_configured()

            result = await _validate_connection(url, token)
            if result is None:
                return self.async_create_entry(
                    title=f"OpenChore ({url})",
                    data={CONF_URL: url, CONF_TOKEN: token},
                )
            errors["base"] = result["error"]

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
