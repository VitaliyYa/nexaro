#!/usr/bin/env python3
"""
SmartRent Dev Edge Emulator
Simulates a Home Assistant OS edge node responding to cloud commands.
Subscribes to 'properties/+/+/+/set' and responds with state updates on 'properties/+/+/+/state'.
"""

import json
import logging
import os
import sys
import threading
import time
from pathlib import Path
import paho.mqtt.client as mqtt

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [EdgeEmulator] %(message)s",
)
logger = logging.getLogger("edge_emulator")


def load_env_file():
    """Reads .env from current directory or project root without requiring third-party libraries."""
    candidates = [
        Path.cwd() / ".env",
        Path(__file__).resolve().parent.parent / ".env",
        Path(__file__).resolve().parent / ".env",
    ]
    for env_path in candidates:
        if env_path.is_file():
            logger.info("Loaded environment from %s", env_path)
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, _, v = line.partition("=")
                            k = k.strip()
                            v = v.strip().strip('"').strip("'")
                            if k not in os.environ:
                                os.environ[k] = v
                break
            except Exception as e:
                logger.warning("Failed to read %s: %s", env_path, e)


load_env_file()

MQTT_HOST = os.getenv("MQTT_BROKER_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))
MQTT_USER = os.getenv("MQTT_WORKER_USERNAME", "backend_worker")
MQTT_PASSWORD = os.getenv("MQTT_WORKER_PASSWORD", "")


def on_connect(client, userdata, flags, reason_code, properties=None):
    logger.info("Connected to MQTT broker (%s:%s) with code: %s", MQTT_HOST, MQTT_PORT, reason_code)
    client.subscribe("properties/+/+/+/set", qos=1)
    logger.info("Subscribed to command topics: properties/+/+/+/set")


def handle_device_command(client: mqtt.Client, topic: str, payload_str: str):
    # Topic pattern: properties/<property_id>/<device_type>/<device_id>/set
    parts = topic.split("/")
    if len(parts) != 5:
        return

    property_id, device_type, device_id = parts[1], parts[2], parts[3]
    state_topic = f"properties/{property_id}/{device_type}/{device_id}/state"

    logger.info("Received command on [%s]: %s", topic, payload_str)

    # Simulate realistic 0.8s physical actuator response delay
    time.sleep(0.8)

    try:
        data = json.loads(payload_str)
    except Exception:
        data = payload_str.strip()

    state_payload = {}
    if device_type == "relay":
        val = data.get("command", data.get("state", data)) if isinstance(data, dict) else str(data).strip("\"'")
        state_payload = {"state": str(val).upper()}
    elif device_type == "lock":
        action = (data.get("command") or data.get("action", "")).lower() if isinstance(data, dict) else str(data).lower()
        if action in ("unlock", "unlocked"):
            state_payload = {"state": "unlocked", "lock_state": "unlocked", "battery": 95}
        else:
            state_payload = {"state": "locked", "lock_state": "locked", "battery": 95}
    elif device_type == "valve":
        action = (data.get("command") or data.get("action", "")).lower() if isinstance(data, dict) else str(data).lower()
        state_payload = {"state": "closed" if action in ("close", "closed") else "open", "leak_detected": False}
    elif device_type == "climate":
        state_payload = {
            "current_temperature": 21.5,
            "target_temperature": data.get("target_temperature", 22.0) if isinstance(data, dict) else 22.0,
            "mode": data.get("hvac_mode", data.get("mode", "cool")) if isinstance(data, dict) else "cool",
            "fan_mode": "auto",
        }
    else:
        state_payload = {"state": "OK", "raw": data}

    payload_json = json.dumps(state_payload)
    client.publish(state_topic, payload_json, qos=1, retain=True)
    logger.info("Published confirmed state to [%s]: %s", state_topic, payload_json)


def on_message(client, userdata, msg: mqtt.MQTTMessage):
    payload = msg.payload.decode("utf-8", errors="ignore")
    # Run in thread so sleep doesn't block MQTT network loop
    threading.Thread(target=handle_device_command, args=(client, msg.topic, payload)).start()


def main():
    logger.info("Starting SmartRent Dev Edge Emulator...")
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="smartrent_dev_edge_emulator")
    if MQTT_USER:
        client.username_pw_set(MQTT_USER, MQTT_PASSWORD)

    mqtt_tls_enabled = os.getenv("MQTT_TLS_ENABLED", "true").lower() in ("true", "1", "yes")
    if mqtt_tls_enabled or MQTT_PORT == 8883:
        import ssl
        tls_context = ssl.create_default_context()
        ca_path = os.getenv("MQTT_CA_CERT_PATH")
        if not ca_path:
            dev_ca = Path(__file__).resolve().parent.parent / "edge" / "mosquitto" / "certs" / "ca.crt"
            if dev_ca.exists():
                ca_path = str(dev_ca)

        if ca_path and Path(ca_path).exists():
            tls_context.load_verify_locations(cafile=ca_path)

        tls_context.check_hostname = False
        if not ca_path or not Path(ca_path).exists():
            tls_context.verify_mode = ssl.CERT_NONE

        client.tls_set_context(tls_context)
        logger.info("Configured TLS context for MQTT connection on port %s", MQTT_PORT)

    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    except Exception as e:
        logger.error("Failed to connect to broker: %s", e)
        sys.exit(1)

    try:
        client.loop_forever()
    except KeyboardInterrupt:
        logger.info("Stopping emulator...")
        client.disconnect()


if __name__ == "__main__":
    main()
