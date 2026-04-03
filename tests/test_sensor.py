"""Tests for OpenChore sensor entities."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from custom_components.openchore.coordinator import OpenChoreData
from custom_components.openchore.sensor import (
    OpenChoreCountSensor,
    OpenChorePerChoreSensor,
    OpenChoreUserCountSensor,
    async_setup_entry,
)

from .conftest import MOCK_API_RESPONSE


def test_chore_count_sensor(mock_coordinator, mock_entry_id):
    """Test chore count sensor reports correct state and attributes."""
    sensor = OpenChoreCountSensor(mock_coordinator, mock_entry_id)

    assert sensor.native_value == 2
    assert sensor.extra_state_attributes == {"chores": ["Dishes", "Laundry"]}
    assert sensor.unique_id == f"{mock_entry_id}_chore_count"
    assert sensor.icon == "mdi:clipboard-check-multiple-outline"
    assert sensor.native_unit_of_measurement == "chores"


def test_user_count_sensor(mock_coordinator, mock_entry_id):
    """Test user count sensor reports correct state and attributes."""
    sensor = OpenChoreUserCountSensor(mock_coordinator, mock_entry_id)

    assert sensor.native_value == 2
    assert sensor.extra_state_attributes == {"users": ["Alice", "Bob"]}
    assert sensor.unique_id == f"{mock_entry_id}_user_count"
    assert sensor.icon == "mdi:account-group"
    assert sensor.native_unit_of_measurement == "users"


def test_per_chore_sensors_created(mock_coordinator, mock_entry_id):
    """Test that per-chore sensors are created for each chore."""
    chores = mock_coordinator.data.chores
    sensors = [
        OpenChorePerChoreSensor(mock_coordinator, mock_entry_id, chore)
        for chore in chores
    ]

    assert len(sensors) == 2
    names = [s.name for s in sensors]
    assert "Dishes" in names
    assert "Laundry" in names


def test_per_chore_sensor_trigger_count(mock_coordinator, mock_entry_id):
    """Test that per-chore sensors report correct trigger counts."""
    chores = mock_coordinator.data.chores
    sensors = {
        chore["title"]: OpenChorePerChoreSensor(
            mock_coordinator, mock_entry_id, chore
        )
        for chore in chores
    }

    assert sensors["Dishes"].native_value == 2
    assert sensors["Laundry"].native_value == 1

    dishes_attrs = sensors["Dishes"].extra_state_attributes
    assert dishes_attrs["trigger_uuids"] == ["uuid-dishes-1", "uuid-dishes-2"]
    assert dishes_attrs["title"] == "Dishes"

    laundry_attrs = sensors["Laundry"].extra_state_attributes
    assert laundry_attrs["trigger_uuids"] == ["uuid-laundry-1"]
    assert laundry_attrs["title"] == "Laundry"


def test_sensor_device_info(mock_coordinator, mock_entry_id):
    """Test that sensors have correct device_info."""
    sensor = OpenChoreCountSensor(mock_coordinator, mock_entry_id)
    device_info = sensor.device_info

    assert ("openchore", "http://openchore.local") in device_info["identifiers"]
    assert device_info["name"] == "OpenChore"
    assert device_info["manufacturer"] == "OpenChore"


def test_sensors_handle_no_data(mock_entry_id):
    """Test that sensors return 0/empty when coordinator.data is None."""
    coordinator = MagicMock()
    coordinator.data = None
    coordinator.base_url = "http://openchore.local"
    coordinator.async_add_listener = MagicMock(return_value=lambda: None)

    count_sensor = OpenChoreCountSensor(coordinator, mock_entry_id)
    assert count_sensor.native_value == 0
    assert count_sensor.extra_state_attributes == {"chores": []}

    user_sensor = OpenChoreUserCountSensor(coordinator, mock_entry_id)
    assert user_sensor.native_value == 0
    assert user_sensor.extra_state_attributes == {"users": []}

    # Per-chore sensor with no data
    chore = {"title": "Test", "triggers": [{"uuid": "uuid-test"}]}
    per_chore = OpenChorePerChoreSensor(coordinator, mock_entry_id, chore)
    assert per_chore.native_value == 0
    assert per_chore.extra_state_attributes == {
        "trigger_uuids": [],
        "title": "Test",
    }


@pytest.mark.asyncio
async def test_async_setup_entry(mock_coordinator, mock_entry_id):
    """Test that async_setup_entry creates all expected entities."""
    mock_entry = MagicMock()
    mock_entry.entry_id = mock_entry_id
    mock_entry.runtime_data = mock_coordinator

    added_entities = []

    def capture_entities(entities):
        added_entities.extend(entities)

    await async_setup_entry(MagicMock(), mock_entry, capture_entities)

    # Should create: 1 chore count + 1 user count + 2 per-chore = 4 total
    assert len(added_entities) == 4

    types = [type(e).__name__ for e in added_entities]
    assert types.count("OpenChoreCountSensor") == 1
    assert types.count("OpenChoreUserCountSensor") == 1
    assert types.count("OpenChorePerChoreSensor") == 2
