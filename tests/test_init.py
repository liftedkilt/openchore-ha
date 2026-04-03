"""Tests for OpenChore __init__ (options update listener)."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import MagicMock

import pytest

from custom_components.openchore.const import (
    CONF_SCAN_INTERVAL,
    CONF_TOKEN,
    CONF_URL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)


@pytest.mark.asyncio
async def test_options_update_changes_interval():
    """Verify that changing options updates coordinator.update_interval."""
    from custom_components.openchore import _async_update_options

    coordinator = MagicMock()
    coordinator.update_interval = timedelta(seconds=DEFAULT_SCAN_INTERVAL)

    entry = MagicMock()
    entry.data = {CONF_URL: "http://openchore.local", CONF_TOKEN: "tok"}
    entry.options = {CONF_SCAN_INTERVAL: 60}
    entry.runtime_data = coordinator

    hass = MagicMock()

    await _async_update_options(hass, entry)

    assert coordinator.update_interval == timedelta(seconds=60)


@pytest.mark.asyncio
async def test_options_update_uses_default_when_not_set():
    """Verify that missing option falls back to DEFAULT_SCAN_INTERVAL."""
    from custom_components.openchore import _async_update_options

    coordinator = MagicMock()
    coordinator.update_interval = timedelta(seconds=60)

    entry = MagicMock()
    entry.data = {CONF_URL: "http://openchore.local", CONF_TOKEN: "tok"}
    entry.options = {}  # no scan_interval set
    entry.runtime_data = coordinator

    hass = MagicMock()

    await _async_update_options(hass, entry)

    assert coordinator.update_interval == timedelta(seconds=DEFAULT_SCAN_INTERVAL)
