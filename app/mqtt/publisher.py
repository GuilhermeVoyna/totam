import json
import logging
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

from app.config.settings import (
    GROUP,
    TOTAM_HOSTNAME,
    HEARTBEAT_INTERVAL,
)


logger = logging.getLogger(__name__)


class MQTTPublisher:

    def __init__(
        self,
        client,
        mac,
        status_topic,
        heartbeat_topic,
    ):
        self.client = client
        self.mac = mac
        self.status_topic = status_topic
        self.heartbeat_topic = heartbeat_topic

    def status_payload(self, status):
        return json.dumps({
            "group": GROUP,
            "status": status,
            "mac": self.mac,
            "hostname": TOTAM_HOSTNAME,
        })

    def publish_status(self, status):
        result = self.client.publish(
            topic=self.status_topic,
            payload=self.status_payload(status),
            qos=1,
            retain=True,
        )

        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            logger.error(
                "Failed to queue status '%s': rc=%s",
                status,
                result.rc,
            )
            return False

        logger.info(
            "Status queued: topic=%s status=%s",
            self.status_topic,
            status,
        )
        return True

    def publish_heartbeat(self, mac=None):
        if HEARTBEAT_INTERVAL <= 0:
            return False

        payload = {
            "hostname": TOTAM_HOSTNAME,
            "mac": self.mac,
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
        }

        result = self.client.publish(
            topic=self.heartbeat_topic,
            payload=json.dumps(payload),
            qos=1,
            retain=False,
        )

        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            logger.error(
                "Failed to queue heartbeat: topic=%s rc=%s",
                self.heartbeat_topic,
                result.rc,
            )
            return False

        logger.info(
            "Heartbeat queued: topic=%s mid=%s",
            self.heartbeat_topic,
            result.mid,
        )
        return True