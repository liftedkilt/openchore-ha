"""Fixtures for OpenChore tests."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from custom_components.openchore.coordinator import OpenChoreData

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
