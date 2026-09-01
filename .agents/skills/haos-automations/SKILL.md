---
name: haos-automations
description: >-
  Guide for configuring Home Assistant OS (HAOS), writing automations and blueprints,
  integrating TTLock smart locks, and implementing autonomous local fallbacks for leak protection in SmartRent.
---

# Home Assistant OS (HAOS) Edge Automations Guide

This skill governs the development of configuration, blueprints, and automations on Edge nodes running **Home Assistant OS** for SmartRent.

---

## 1. Core Principles

1. **Local Autonomy First:** Critical safety automations (e.g. water leak detection → immediate valve shutoff) must operate 100% locally on the Edge node without relying on internet or cloud availability.
2. **Idempotency:** All automations triggered by MQTT commands must be idempotent (re-applying the same command produces the same safe state without errors).
3. **Status Retain:** Edge nodes must publish state updates to MQTT with `retain: true`.

---

## 2. Water Leak & Autonomous Valve Shutoff Blueprint

When a leak sensor detects water:
1. Immediately send close command to the local motorized ball valve.
2. Publish an alert event to the cloud MQTT topic (`properties/<property_id>/water_valve/<device_id>/event`).

```yaml
alias: "Local Water Leak Protection"
description: "Close valve immediately upon leak detection (Local-only priority)"
trigger:
  - platform: state
    entity_id: binary_sensor.water_leak_kitchen
    to: "on"
  - platform: state
    entity_id: binary_sensor.water_leak_bathroom
    to: "on"
action:
  - service: valve.close_valve
    target:
      entity_id: valve.main_water_shutoff
  - service: mqtt.publish
    data:
      topic: "properties/{{ states('sensor.smartrent_property_id') }}/water_valve/main_valve/event"
      payload: '{"event": "leak_detected", "source": "{{ trigger.entity_id }}", "action": "valve_closed"}'
      qos: 1
      retain: false
mode: single
```

---

## 3. MQTT Bridge Pattern for Relays & Switches

For switches with or without physical state feedback:
- Listen on `properties/<property_id>/relay/<device_id>/set`.
- Execute service call on local entity.
- Publish updated state to `properties/<property_id>/relay/<device_id>/state`.

```yaml
alias: "MQTT Relay Bridge: Living Room Lights"
trigger:
  - platform: mqtt
    topic: "properties/+/relay/light_living_room/set"
action:
  - choose:
      - conditions:
          - condition: template
            value_template: "{{ trigger.payload == 'ON' }}"
        sequence:
          - service: switch.turn_on
            target:
              entity_id: switch.living_room_relay
      - conditions:
          - condition: template
            value_template: "{{ trigger.payload == 'OFF' }}"
        sequence:
          - service: switch.turn_off
            target:
              entity_id: switch.living_room_relay
mode: restart
```

---

## 4. TTLock Bridge Standards

- Never transmit plain PINs over unencrypted local channels.
- Keep TTLock local Bluetooth / Gateway integration isolated and synchronize passcode validity windows via backend-issued schedules.
