"""Tests for OpenChore config flow and options flow."""

from __future__ import annotations

from datetime import timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import voluptuous as vol

from custom_components.openchore.config_flow import (
    OpenChoreConfigFlow,
    OpenChoreOptionsFlowHandler,
    _validate_connection,
)
from custom_components.openchore.const import (
    CONF_SCAN_INTERVAL,
    CONF_TOKEN,
    CONF_URL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

# FlowResultType string values (avoid direct homeassistant import in tests
# to prevent import-order issues with older HA versions)
RESULT_TYPE_FORM = "form"
RESULT_TYPE_CREATE_ENTRY = "create_entry"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_config_entry(options: dict[str, Any] | None = None) -> MagicMock:
    """Create a mock config entry with the given options."""
    entry = MagicMock()
    entry.data = {CONF_URL: "http://openchore.local", CONF_TOKEN: "tok123"}
    entry.options = options or {}
    entry.entry_id = "test_entry_id"
    return entry


def _make_options_flow(options: dict[str, Any] | None = None) -> OpenChoreOptionsFlowHandler:
    """Create an options flow handler wired to a mock config entry."""
    flow = OpenChoreOptionsFlowHandler()
    flow.config_entry = _make_mock_config_entry(options)
    # Stub HA internals that the base class uses
    flow.hass = MagicMock()
    flow.flow_id = "test_flow"
    return flow


def _make_config_flow() -> OpenChoreConfigFlow:
    """Create a config flow handler with mocked HA internals."""
    flow = OpenChoreConfigFlow()
    flow.hass = MagicMock()
    flow.flow_id = "test_flow"
    flow.context = {}
    # Stub unique id helpers
    flow.async_set_unique_id = AsyncMock(return_value=None)
    flow._abort_if_unique_id_configured = MagicMock()
    return flow


# ---------------------------------------------------------------------------
# Options flow tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_options_flow_default_values():
    """Test that the options flow init step shows default values."""
    flow = _make_options_flow()
    result = await flow.async_step_init(user_input=None)

    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "init"
    # The schema should have scan_interval with default=300
    schema = result["data_schema"]
    schema_dict = schema.schema
    for key in schema_dict:
        if str(key) == CONF_SCAN_INTERVAL:
            assert key.default() == DEFAULT_SCAN_INTERVAL
            break
    else:
        pytest.fail("scan_interval not found in schema")


@pytest.mark.asyncio
async def test_options_flow_default_values_with_existing_option():
    """Test that the options flow uses the existing option value as default."""
    flow = _make_options_flow(options={CONF_SCAN_INTERVAL: 120})
    result = await flow.async_step_init(user_input=None)

    assert result["type"] == RESULT_TYPE_FORM
    schema = result["data_schema"]
    for key in schema.schema:
        if str(key) == CONF_SCAN_INTERVAL:
            assert key.default() == 120
            break
    else:
        pytest.fail("scan_interval not found in schema")


@pytest.mark.asyncio
async def test_options_flow_update():
    """Test that changing scan interval creates an entry with new value."""
    flow = _make_options_flow()
    result = await flow.async_step_init(user_input={CONF_SCAN_INTERVAL: 60})

    assert result["type"] == RESULT_TYPE_CREATE_ENTRY
    assert result["data"] == {CONF_SCAN_INTERVAL: 60}


@pytest.mark.asyncio
async def test_options_flow_validation():
    """Test that values outside 30-3600 are rejected by the schema."""
    flow = _make_options_flow()
    result = await flow.async_step_init(user_input=None)
    schema = result["data_schema"]

    # Too low
    with pytest.raises(vol.MultipleInvalid):
        schema({CONF_SCAN_INTERVAL: 10})

    # Too high
    with pytest.raises(vol.MultipleInvalid):
        schema({CONF_SCAN_INTERVAL: 5000})

    # Not an int
    with pytest.raises(vol.MultipleInvalid):
        schema({CONF_SCAN_INTERVAL: "abc"})

    # Valid boundaries
    assert schema({CONF_SCAN_INTERVAL: 30}) == {CONF_SCAN_INTERVAL: 30}
    assert schema({CONF_SCAN_INTERVAL: 3600}) == {CONF_SCAN_INTERVAL: 3600}


# ---------------------------------------------------------------------------
# Config flow tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_user_step_success():
    """Test that a successful connection creates an entry."""
    flow = _make_config_flow()

    with patch(
        "custom_components.openchore.config_flow._validate_connection",
        return_value=None,
    ):
        result = await flow.async_step_user(
            user_input={CONF_URL: "http://openchore.local", CONF_TOKEN: "good_token"}
        )

    assert result["type"] == RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == "OpenChore (http://openchore.local)"
    assert result["data"] == {
        CONF_URL: "http://openchore.local",
        CONF_TOKEN: "good_token",
    }


@pytest.mark.asyncio
async def test_user_step_shows_form_initially():
    """Test that the user step shows a form when no input is provided."""
    flow = _make_config_flow()
    result = await flow.async_step_user(user_input=None)

    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}


@pytest.mark.asyncio
async def test_user_step_invalid_auth():
    """Test that a 401 response shows invalid_auth error."""
    flow = _make_config_flow()

    with patch(
        "custom_components.openchore.config_flow._validate_connection",
        return_value={"error": "invalid_auth"},
    ):
        result = await flow.async_step_user(
            user_input={CONF_URL: "http://openchore.local", CONF_TOKEN: "bad_token"}
        )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["errors"] == {"base": "invalid_auth"}


@pytest.mark.asyncio
async def test_user_step_cannot_connect():
    """Test that a connection error shows cannot_connect error."""
    flow = _make_config_flow()

    with patch(
        "custom_components.openchore.config_flow._validate_connection",
        return_value={"error": "cannot_connect"},
    ):
        result = await flow.async_step_user(
            user_input={CONF_URL: "http://openchore.local", CONF_TOKEN: "tok"}
        )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["errors"] == {"base": "cannot_connect"}


# ---------------------------------------------------------------------------
# async_get_options_flow test
# ---------------------------------------------------------------------------

def test_async_get_options_flow():
    """Test that the config flow returns an options flow handler."""
    entry = _make_mock_config_entry()
    handler = OpenChoreConfigFlow.async_get_options_flow(entry)
    assert isinstance(handler, OpenChoreOptionsFlowHandler)


# ---------------------------------------------------------------------------
# _validate_connection integration-style tests (uses real aiohttp)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_validate_connection_success():
    """Test _validate_connection returns None on 200."""
    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=False)

    mock_session = AsyncMock()
    mock_session.get = MagicMock(return_value=mock_resp)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        result = await _validate_connection("http://test.local", "token")

    assert result is None


@pytest.mark.asyncio
async def test_validate_connection_401():
    """Test _validate_connection returns invalid_auth on 401."""
    mock_resp = AsyncMock()
    mock_resp.status = 401
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=False)

    mock_session = AsyncMock()
    mock_session.get = MagicMock(return_value=mock_resp)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        result = await _validate_connection("http://test.local", "token")

    assert result == {"error": "invalid_auth"}


@pytest.mark.asyncio
async def test_validate_connection_network_error():
    """Test _validate_connection returns cannot_connect on aiohttp error."""
    import aiohttp

    mock_session = AsyncMock()
    mock_session.get = MagicMock(side_effect=aiohttp.ClientError("fail"))
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        result = await _validate_connection("http://test.local", "token")

    assert result == {"error": "cannot_connect"}
