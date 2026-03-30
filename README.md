# OpenChore Home Assistant Integration

A custom Home Assistant integration for [OpenChore](https://github.com/liftedkilt/openchore), a chore management app. This integration lets you trigger chores from Home Assistant automations -- for example, automatically assigning a "Take out the trash" chore when a sensor detects the trash is full.

## Features

- **Config Flow UI** -- set up the integration entirely from the HA UI
- **Automatic Discovery** -- polls the OpenChore server for available chores, triggers, and users
- **`openchore.trigger_chore` Service** -- fire a chore trigger from any automation, script, or the Developer Tools
- **Validation** -- validates trigger UUIDs and usernames against live server data before firing

## Requirements

- OpenChore server with API token authentication enabled
- At least one chore with an enabled trigger configured in the OpenChore admin panel

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Click the three dots in the top right and select **Custom repositories**
3. Add `https://github.com/liftedkilt/openchore-ha` with category **Integration**
4. Search for "OpenChore" and install it
5. Restart Home Assistant

### Manual

1. Copy the `custom_components/openchore` directory into your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings > Devices & Services > Add Integration**
2. Search for "OpenChore"
3. Enter your OpenChore server URL (e.g. `http://192.168.1.100:8080`)
4. Enter an API token (create one in the OpenChore admin panel under API Tokens)

## Usage

### Service: `openchore.trigger_chore`

This service fires a chore trigger, creating a one-off schedule for today.

| Field | Required | Description |
|-------|----------|-------------|
| `trigger_uuid` | Yes | The UUID of the chore trigger to fire |
| `assign_to` | No | Username to assign the chore to (uses trigger's default if omitted) |
| `due_by` | No | Time the chore must be completed by (e.g. `18:00`) |
| `available_at` | No | Time the chore becomes available (e.g. `08:00`) |

### Example Automation

```yaml
automation:
  - alias: "Assign trash chore when bin is full"
    trigger:
      - platform: state
        entity_id: binary_sensor.trash_bin_full
        to: "on"
    action:
      - service: openchore.trigger_chore
        data:
          trigger_uuid: "abc123def456..."
          assign_to: "alice"
          due_by: "18:00"
```

### Finding Trigger UUIDs

Trigger UUIDs are shown in the OpenChore admin panel under each chore's trigger configuration. You can also call the discovery endpoint directly:

```
GET http://your-server:8080/api/chores/triggerable
Authorization: Bearer <your-token>
```

## How It Works

1. On setup, the integration validates your credentials against the OpenChore discovery endpoint
2. A `DataUpdateCoordinator` polls `/api/chores/triggerable` every 5 minutes to keep the list of available chores, triggers, and users current
3. When `openchore.trigger_chore` is called, it validates inputs against the cached data, then POSTs to `/api/hooks/trigger/{uuid}` with the provided parameters
4. The OpenChore server creates a one-off chore schedule for today and returns confirmation

## Troubleshooting

- **"Failed to connect"** during setup -- verify the URL is reachable from your HA instance and includes the port if needed
- **"Invalid API token"** -- ensure the token was created in the OpenChore admin panel and has not been revoked
- **"Unknown trigger UUID"** -- the trigger may have been deleted or disabled; check the OpenChore admin panel
- **"Trigger is in cooldown"** -- the trigger has a cooldown period configured and was recently fired; wait for the cooldown to expire
