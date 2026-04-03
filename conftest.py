"""Root conftest that mocks homeassistant packages before any imports."""

import sys
from types import ModuleType
from unittest.mock import MagicMock


def _make_module(name, attrs=None):
    mod = ModuleType(name)
    if attrs:
        for k, v in attrs.items():
            setattr(mod, k, v)
    sys.modules[name] = mod
    return mod


# Only mock if homeassistant is not installed
if "homeassistant" not in sys.modules:
    # Sentinel classes / enums we actually use in code
    class _SensorEntity:
        _attr_has_entity_name = False
        _attr_unique_id = None
        _attr_name = None
        _attr_state_class = None
        _attr_native_unit_of_measurement = None
        _attr_icon = None

        @property
        def unique_id(self):
            return self._attr_unique_id

        @property
        def name(self):
            return self._attr_name

        @property
        def icon(self):
            return self._attr_icon

        @property
        def native_unit_of_measurement(self):
            return self._attr_native_unit_of_measurement

        @property
        def state_class(self):
            return self._attr_state_class

    class _SensorStateClass:
        MEASUREMENT = "measurement"

    class _CoordinatorEntity:
        def __class_getitem__(cls, item):
            return cls

        def __init__(self, coordinator, *args, **kwargs):
            self.coordinator = coordinator

    class _DeviceEntryType:
        SERVICE = "service"

    class _DeviceInfo(dict):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)

    class _Platform:
        SENSOR = "sensor"

    class _DataUpdateCoordinator:
        def __class_getitem__(cls, item):
            return cls

        def __init__(self, hass, logger, *, name, update_interval):
            self.hass = hass
            self.name = name
            self.update_interval = update_interval

    class _UpdateFailed(Exception):
        pass

    class _ConfigEntry:
        def __class_getitem__(cls, item):
            return cls

    class _HomeAssistantError(Exception):
        pass

    class _ServiceValidationError(Exception):
        pass

    # Build module tree
    ha = _make_module("homeassistant")
    _make_module("homeassistant.core", {"HomeAssistant": MagicMock, "ServiceCall": MagicMock, "callback": lambda f: f})
    _make_module("homeassistant.config_entries", {"ConfigEntry": _ConfigEntry, "ConfigFlow": MagicMock, "ConfigFlowResult": MagicMock, "OptionsFlow": MagicMock})
    _make_module("homeassistant.const", {"Platform": _Platform})
    _make_module("homeassistant.exceptions", {"HomeAssistantError": _HomeAssistantError, "ServiceValidationError": _ServiceValidationError})

    ha_helpers = _make_module("homeassistant.helpers")
    _make_module("homeassistant.helpers.config_validation", {"string": str})
    _make_module("homeassistant.helpers.service", {"async_set_service_schema": MagicMock()})
    _make_module("homeassistant.helpers.entity_platform", {"AddEntitiesCallback": MagicMock})
    _make_module("homeassistant.helpers.device_registry", {
        "DeviceEntryType": _DeviceEntryType,
        "DeviceInfo": _DeviceInfo,
    })
    _make_module("homeassistant.helpers.update_coordinator", {
        "CoordinatorEntity": _CoordinatorEntity,
        "DataUpdateCoordinator": _DataUpdateCoordinator,
        "UpdateFailed": _UpdateFailed,
    })

    _make_module("homeassistant.components")
    _make_module("homeassistant.components.sensor", {
        "SensorEntity": _SensorEntity,
        "SensorStateClass": _SensorStateClass,
    })
