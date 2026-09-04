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
import time
import threading
from dotenv import load_dotenv
import paho.mqtt.client as mqtt

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [EdgeEmulator] %(message)s",
)
logger = logging.getLogger("edge_emulator")

load_dotenv()

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
        # Raw string or dict
        val = data.get("state", data) if isinstance(data, dict) else str(data).strip("\"'")
        state_payload = {"state": val.upper()}
    elif device_type == "lock":
        action = data.get("action", "").lower() if isinstance(data, dict) else str(data).lower()
        if action == "unlock":
            state_payload = {"state": "unlocked", "lock_state": "unlocked", "battery": 95}
        else:
            state_payload = {"state": "locked", "lock_state": "locked", "battery": 95}
    elif device_type == "valve":
        action = data.get("action", "").lower() if isinstance(data, dict) else str(data).lower()
        state_payload = {"state": "closed" if action == "close" else "open", "leak_detected": False}
    elif device_type == "climate":
        state_payload = {
            "current_temperature": 21.5,
            "target_temperature": data.get("target_temperature", 22.0) if isinstance(data, dict) else 22.0,
            "mode": data.get("mode", "cool") if isinstance(data, dict) else "cool",
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
