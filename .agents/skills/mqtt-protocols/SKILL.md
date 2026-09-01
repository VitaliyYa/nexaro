---
name: mqtt-protocols
description: >-
  Guidelines, schemas, and best practices for MQTT topic structure, Mosquitto broker setup,
  dynamic ACL tenant isolation, QoS/Retain rules, and IoT worker integration in SmartRent.
---

# MQTT Protocols & Mosquitto Architecture Guide

This skill governs the design, implementation, and security of the MQTT messaging layer in the **SmartRent** B2B SaaS platform.

---

## 1. Topic Namespace Architecture

All MQTT topics must strictly follow the hierarchical namespace to enforce tenant isolation and predictable routing:

```
properties/<property_id>/<device_type>/<device_id>/<action>
```

### Topic Types

| Action | Direction | Description | Example |
| :--- | :--- | :--- | :--- |
| `set` | **Cloud → Edge** | Command sent to an IoT device or HAOS bridge | `properties/prop_123/relay/switch_main/set` |
| `state` | **Edge → Cloud** | Reported physical state of an IoT device | `properties/prop_123/relay/switch_main/state` |
| `event` | **Edge → Cloud** | Asynchronous events (e.g. badge scanned, water leak triggered) | `properties/prop_123/lock/front_door/event` |
| `availability` | **Edge → Cloud** | LWT (Last Will and Testament) node health | `properties/prop_123/node/gateway/availability` |

---

## 2. QoS and Retain Flags Policy

To prevent state desynchronization and unintended command re-execution upon reconnect:

1. **Commands (`/set`):**
   - **QoS:** `1` (At least once delivery)
   - **Retain:** `false` (**NEVER** retain commands to avoid re-triggering actions on reconnect).

2. **State Updates (`/state`):**
   - **QoS:** `1` (Guaranteed status sync)
   - **Retain:** `true` (Always retain the latest physical state for fast UI initialization).

3. **Telemetry & Periodic Metrics:**
   - **QoS:** `0` (Best effort, non-critical)
   - **Retain:** `false`.

4. **Node Availability (LWT):**
   - **QoS:** `1`
   - **Retain:** `true` (Payload: `online` on connect, `offline` in LWT message).

---

## 3. Mosquitto Security & Multi-Tenant ACLs

### Dynamic ACL Rules (per Edge Node / Property)

Every Edge node (HAOS instance) has its own unique username and password. Access is strictly scoped to its own property ID:

```acl
# Edge Node ACL for Property prop_123
user edge_prop_123
topic write properties/prop_123/+/+/state
topic write properties/prop_123/+/+/event
topic write properties/prop_123/node/+/availability
topic read properties/prop_123/+/+/set

# Cloud Backend Service ACL
user backend_worker
topic read properties/+/+/+/state
topic read properties/+/+/+/event
topic read properties/+/node/+/availability
topic write properties/+/+/+/set
```

> [!CAUTION]
> Edge nodes must **never** be granted wildcard read/write access across other `property_id` hierarchies.

---

## 4. Backend MQTT Worker Pattern (Python / `paho-mqtt`)

When implementing the background MQTT Worker in FastAPI:

1. Maintain persistent connection with TLS (Port `8883`) using verified CA certificates.
2. Route incoming `/state` and `/event` payloads to database batching or audit logging asynchronously.
3. Validate all incoming and outgoing JSON payloads against JSON Schemas located in `schemas/`.
