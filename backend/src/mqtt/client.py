import json
import logging
import ssl
from typing import Any

import paho.mqtt.client as mqtt

from src.config import Settings, get_settings

logger = logging.getLogger("smartrent.mqtt")


class MqttService:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.client: mqtt.Client | None = None
        self._connected = False

    def create_client(self) -> mqtt.Client:
        # Paho MQTT Client Callback API v2 compatibility
        client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=f"smartrent-backend-{self.settings.MQTT_WORKER_USERNAME}",
            clean_session=False,
        )

        client.username_pw_set(
            username=self.settings.MQTT_WORKER_USERNAME,
            password=self.settings.MQTT_WORKER_PASSWORD,
        )

        if self.settings.MQTT_TLS_ENABLED:
            tls_context = ssl.create_default_context()
            if self.settings.MQTT_CA_CERT_PATH:
                tls_context.load_verify_locations(cafile=self.settings.MQTT_CA_CERT_PATH)
            if self.settings.MQTT_CLIENT_CERT_PATH and self.settings.MQTT_CLIENT_KEY_PATH:
                tls_context.load_cert_chain(
                    certfile=self.settings.MQTT_CLIENT_CERT_PATH,
                    keyfile=self.settings.MQTT_CLIENT_KEY_PATH,
                )
            client.tls_set_context(tls_context)

        client.on_connect = self._on_connect
        client.on_disconnect = self._on_disconnect
        return client

    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        if reason_code == 0:
            self._connected = True
            logger.info(
                "Connected to MQTT Broker (%s:%s)",
                self.settings.MQTT_BROKER_HOST,
                self.settings.MQTT_BROKER_PORT,
            )
        else:
            self._connected = False
            logger.error("Failed to connect to MQTT broker, return code: %s", reason_code)

    def _on_disconnect(self, client, userdata, flags, reason_code, properties=None):
        self._connected = False
        logger.warning("Disconnected from MQTT Broker: %s", reason_code)

    def start(self):
        if not self.client:
            self.client = self.create_client()
        try:
            self.client.connect_async(
                host=self.settings.MQTT_BROKER_HOST,
                port=self.settings.MQTT_BROKER_PORT,
                keepalive=self.settings.MQTT_KEEPALIVE,
            )
            self.client.loop_start()
        except Exception as e:
            logger.warning(
                "Could not immediately connect to MQTT broker (%s). Running in offline/retry mode.",
                e,
            )

    def stop(self):
        if self.client:
            try:
                self.client.loop_stop()
                self.client.disconnect()
            except Exception as e:
                logger.error("Error stopping MQTT client: %s", e)
            self._connected = False

    def publish_command(
        self,
        topic: str,
        payload: dict[str, Any] | str,
        qos: int = 1,
        retain: bool = False,
    ) -> bool:
        """
        Publishes a command to the MQTT broker.
        Strictly enforces QoS=1 and retain=False for commands.
        """
        if not self.client:
            logger.error("MQTT client is not initialized")
            return False

        payload_str = payload if isinstance(payload, str) else json.dumps(payload)
        logger.info(
            "Publishing MQTT command -> Topic: %s, Payload: %s, QoS: %s, Retain: %s",
            topic,
            payload_str,
            qos,
            retain,
        )
        msg_info = self.client.publish(topic, payload_str, qos=qos, retain=retain)
        return msg_info.rc == mqtt.MQTT_ERR_SUCCESS

    @property
    def is_connected(self) -> bool:
        return self._connected


# Global singleton instance for application lifespan
mqtt_service = MqttService()


def get_mqtt_service() -> MqttService:
    return mqtt_service
