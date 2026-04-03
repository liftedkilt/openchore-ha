"""Fixtures for OpenChore tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.openchore.const import CONF_TOKEN, CONF_URL, DOMAIN
from custom_components.openchore.coordinator import OpenChoreData

MOCK_CONFIG_DATA = {
    CONF_URL: "http://openchore.local",
    CONF_TOKEN: "test-token-123",
}

MOCK_API_RESPONSE = {
    "chores": [
        {
            "title": "Dishes",
            "triggers": [
                {"uuid": "uuid-dishes-1"},
                {"uuid": "uuid-dishes-2"},
            ],
        },
        {
            "title": "Laundry",
            "triggers": [
                {"uuid": "uuid-laundry-1"},
            ],
        },
    ],
    "users": [
        {"name": "Alice"},
        {"name": "Bob"},
    ],
}


@pytest.fixture
def mock_coordinator():
    """Return a mock coordinator with sample data."""
    coordinator = MagicMock()
    coordinator.data = OpenChoreData(MOCK_API_RESPONSE)
    coordinator.base_url = "http://openchore.local"
    coordinator.async_add_listener = MagicMock(return_value=lambda: None)
    return coordinator


@pytest.fixture
def mock_entry_id():
    """Return a mock config entry ID."""
    return "test_entry_id"


@pytest.fixture
def mock_setup_entry():
    """Patch async_setup_entry to return True (skip full integration setup)."""
    with patch(
        "custom_components.openchore.async_setup_entry",
        return_value=True,
    ) as mock:
        yield mock


@pytest.fixture
def mock_config_data():
    """Return sample config entry data."""
    return dict(MOCK_CONFIG_DATA)
