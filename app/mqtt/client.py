import logging

import paho.mqtt.client as mqtt

from app.config.settings import (
    TOTAM_HOSTNAME,
    MQTT_USERNAME,
    MQTT_PASSWORD,
)
from app.mqtt.topics import (
    get_command_topic,
    get_status_topic,
    get_heartbeat_topic,
)
from app.mqtt.callbacks import MQTTCallbacks
from app.mqtt.connection import MQTTConnection
from app.mqtt.publisher import MQTTPublisher


logger = logging.getLogger(__name__)


class MQTTClient:

    def __init__(self, controller, mac):
        self.controller = controller
        self.mac = mac

        self.command_topic = get_command_topic(
            TOTAM_HOSTNAME
        )
        self.status_topic = get_status_topic(
            TOTAM_HOSTNAME
        )
        self.heartbeat_topic = get_heartbeat_topic(
            TOTAM_HOSTNAME
        )

        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=f"{TOTAM_HOSTNAME}-{mac}",
            protocol=mqtt.MQTTv5,
        )

        self.publisher = MQTTPublisher(
            client=self.client,
            mac=mac,
            status_topic=self.status_topic,
            heartbeat_topic=self.heartbeat_topic,
        )

        self.callbacks = MQTTCallbacks(
            client=self.client,
            controller=self.controller,
            publisher=self.publisher,
            command_topic=self.command_topic,
        )

        self._configure()

        self.connection = MQTTConnection(
            client=self.client,
            callbacks=self.callbacks,
            publisher=self.publisher,
        )

    def _configure(self):
        self.client.username_pw_set(
            MQTT_USERNAME,
            MQTT_PASSWORD,
        )

        self.client.tls_set()

        self.client.will_set(
            topic=self.status_topic,
            payload=self.publisher.status_payload("offline"),
            qos=1,
            retain=True,
        )

        self.callbacks.register()

    def start(self):
        self.connection.start()

    def disconnect(self):
        self.connection.disconnect()