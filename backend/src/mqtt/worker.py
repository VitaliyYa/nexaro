import json
import logging
from datetime import UTC, datetime
from typing import Any

import paho.mqtt.client as mqtt

from src.auth.supabase import get_supabase_admin_client
from src.config import Settings, get_settings
from src.schemas import (
    ClimateStatePayload,
    LockStatePayload,
    NodeAvailabilityPayload,
    RelayStatePayload,
    ValveEventPayload,
)

logger = logging.getLogger("smartrent.mqtt_worker")


def parse_and_validate_payload(device_type: str, action: str, raw_payload: str | bytes) -> dict[str, Any]:
    """
    Parses and validates incoming MQTT payload JSON against Pydantic models.
    Falls back to raw parsed JSON if schema is not explicitly defined.
    """
    try:
        data = json.loads(raw_payload)
    except Exception as e:
        logger.warning("Failed to decode JSON payload: %s", e)
        return {"raw": str(raw_payload)}

    try:
        if action == "state":
            if device_type == "lock":
                return LockStatePayload.model_validate(data).model_dump(mode="json")
            elif device_type == "relay":
                return RelayStatePayload.model_validate(data).model_dump(mode="json")
            elif device_type == "climate":
                return ClimateStatePayload.model_validate(data).model_dump(mode="json")
        elif action == "event":
            if device_type in ("valve", "sensor"):
                return ValveEventPayload.model_validate(data).model_dump(mode="json")
        elif action == "availability":
            return NodeAvailabilityPayload.model_validate(data).model_dump(mode="json")
    except Exception as e:
        logger.warning("Payload schema validation error for %s/%s: %s", device_type, action, e)

    return data


class MqttWorker:
    def __init__(self, settings: Settings | None = None, admin_client: Any = None):
        self.settings = settings or get_settings()
        self._admin_client = admin_client
        self.client: mqtt.Client | None = None

    @property
    def admin_db(self):
        if self._admin_client is None:
            self._admin_client = get_supabase_admin_client(self.settings)
        return self._admin_client

    def on_connect(self, client, userdata, flags, reason_code, properties=None):
        if reason_code == 0 or not getattr(reason_code, "is_failure", True):
            logger.info("MQTT Worker subscribed to telemetry topics")
            client.subscribe("properties/+/+/+/state", qos=1)
            client.subscribe("properties/+/+/+/event", qos=1)
            client.subscribe("properties/+/node/+/availability", qos=1)
        else:
            logger.error("MQTT Worker subscription connect failure: %s", reason_code)

    def on_message(self, client, userdata, msg: mqtt.MQTTMessage):
        topic = msg.topic
        payload_str = msg.payload.decode("utf-8", errors="ignore")
        logger.debug("Received MQTT message on %s: %s", topic, payload_str)

        try:
            self.process_message(topic, payload_str)
        except Exception as e:
            logger.error("Error processing MQTT message on topic %s: %s", topic, e, exc_info=True)

    def process_message(self, topic: str, raw_payload: str) -> None:
        """
        Extracts topic tokens, validates data, and writes to Supabase device_logs and updates devices.
        """
        parts = topic.split("/")
        # Pattern 1: properties/<property_id>/<device_type>/<device_id>/<action>
        # Pattern 2: properties/<property_id>/node/<node_id>/availability
        if len(parts) < 5 or parts[0] != "properties":
            logger.warning("Ignoring invalid topic format: %s", topic)
            return

        property_id = parts[1]
        device_type = parts[2]
        device_id = parts[3]
        action = parts[4]

        validated_payload = parse_and_validate_payload(device_type, action, raw_payload)
        now_iso = datetime.now(UTC).isoformat()

        # 1. Ingest into device_logs using service role client
        try:
            log_entry = {
                "property_id": property_id,
                "device_id": device_id if device_type != "node" else None,
                "topic": topic,
                "event_type": action,
                "payload": validated_payload,
                "created_at": now_iso,
            }
            self.admin_db.table("device_logs").insert(log_entry).execute()
        except Exception as e:
            logger.error("Failed to insert telemetry into device_logs: %s", e)

        # 2. Update device last_seen and status in devices table
        if device_type != "node" and action == "state":
            try:
                self.admin_db.table("devices").update(
                    {
                        "last_seen": now_iso,
                        "settings": validated_payload,
                    }
                ).eq("property_id", property_id).eq("id", device_id).execute()
            except Exception as e:
                logger.debug("Failed to update devices table (might not exist yet): %s", e)
