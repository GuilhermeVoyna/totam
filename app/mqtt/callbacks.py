import logging

import paho.mqtt.client as mqtt

from app.mqtt.topics import BROADCAST_TOPIC


logger = logging.getLogger(__name__)


class MQTTCallbacks:

    def __init__(
        self,
        client,
        controller,
        publisher,
        command_topic,
    ):
        self.client = client
        self.controller = controller
        self.publisher = publisher
        self.command_topic = command_topic

        self.connection_error = None

    def register(self):
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message

    def on_connect(
        self,
        _client,
        _userdata,
        _flags,
        reason_code,
        _properties,
    ):
        if reason_code.is_failure:
            self.connection_error = str(reason_code)

            logger.error(
                "MQTT connection rejected: %s",
                reason_code,
            )
            return

        self.connection_error = None

        logger.info("MQTT connected")

        self._subscribe_topics()
        self.publisher.publish_status("online")
        self.publisher.publish_heartbeat()

    def on_disconnect(
        self,
        _client,
        _userdata,
        _disconnect_flags,
        reason_code,
        _properties,
    ):
        logger.warning(
            "MQTT disconnected: %s",
            reason_code,
        )

    def on_message(
        self,
        _client,
        _userdata,
        msg,
    ):
        try:
            payload = msg.payload.decode("utf-8")
        except UnicodeDecodeError:
            logger.warning(
                "Invalid UTF-8 payload on topic %s",
                msg.topic,
            )
            return

        if msg.topic not in (
            self.command_topic,
            BROADCAST_TOPIC,
        ):
            return

        logger.info(
            "Command received: topic=%s payload=%s",
            msg.topic,
            payload,
        )

        try:
            self.controller.process_command(payload)
        except Exception:
            logger.exception(
                "Error processing command",
            )

    def _subscribe_topics(self):
        for topic in (
            self.command_topic,
            BROADCAST_TOPIC,
        ):
            result, _ = self.client.subscribe(
                topic,
                qos=1,
            )

            if result != mqtt.MQTT_ERR_SUCCESS:
                logger.error(
                    "Failed to subscribe to %s: %s",
                    topic,
                    result,
                )
                continue

            logger.info(
                "Subscription requested: %s",
                topic,
            )