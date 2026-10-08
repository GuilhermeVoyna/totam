import json
import logging
import ssl
import time
import uuid

import paho.mqtt.client as mqtt

from config.settings import (
    GROUP,
    TOTAM_HOSTNAME,
    MQTT_BROKER,
    MQTT_PASSWORD,
    MQTT_PORT,
    MQTT_USERNAME,
    MQTT_MAX_RETRIES,
    MQTT_RETRY_INITIAL_DELAY,
    MQTT_RETRY_MAX_DELAY,
)
from mqtt.topics import (
    BROADCAST_TOPIC,
    get_command_topic,
    get_status_topic,
)


logger = logging.getLogger(__name__)


class MQTTClient:

    def __init__(self, controller):

        self.controller = controller

        self._connection_error = None

        self.mac = self._get_mac()

        self.command_topic = get_command_topic(
            TOTAM_HOSTNAME
        )

        self.status_topic = get_status_topic(
            TOTAM_HOSTNAME
        )

        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=f"{TOTAM_HOSTNAME}-{self.mac}",
            protocol=mqtt.MQTTv5,
        )

        self._configure()

    # =========================================================
    # CONFIGURATION
    # =========================================================

    def _configure(self):

        self.client.username_pw_set(
            MQTT_USERNAME,
            MQTT_PASSWORD,
        )

        self.client.tls_set(
            tls_version=ssl.PROTOCOL_TLS,
        )

        # Last Will and Testament
        self.client.will_set(
            topic=self.status_topic,
            payload=self._get_status_payload("offline"),
            qos=1,
            retain=True,
        )

        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

    # =========================================================
    # MQTT CALLBACKS
    # =========================================================

    def _on_connect(
        self,
        _client,
        _userdata,
        _flags,
        reason_code,
        _properties,
    ):
        if reason_code.is_failure:
            self._connection_error = str(reason_code)

            logger.error(
                "MQTT connection rejected: %s",
                reason_code,
            )
            return

        self._connection_error = None

        logger.info("MQTT connected")

        self._subscribe_topics()
        self._publish_online()

    def _on_disconnect(
        self,
        _client,
        _userdata,
        _disconnect_flags,
        reason_code,
        _properties,
    ):
        logger.warning(
            "Disconnected from MQTT: %s",
            reason_code,
        )

    def _on_message(
        self,
        _client,
        _userdata,
        msg,
    ):
        try:
            payload = msg.payload.decode("utf-8")

        except UnicodeDecodeError:
            logger.warning(
                "Invalid UTF-8 payload received from topic %s",
                msg.topic,
            )
            return

        logger.info(
            "MQTT message | topic=%s | payload=%s",
            msg.topic,
            payload,
        )

        if msg.topic not in (
            self.command_topic,
            BROADCAST_TOPIC,
        ):
            return

        self.controller.process_command(payload)

    # =========================================================
    # SUBSCRIPTIONS
    # =========================================================

    def _subscribe_topics(self):

        topics = (
            self.command_topic,
            BROADCAST_TOPIC,
        )

        for topic in topics:

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
                "Subscribed to: %s",
                topic,
            )

    # =========================================================
    # STATUS
    # =========================================================

    def _publish_online(self):

        result = self.client.publish(
            topic=self.status_topic,
            payload=self._get_status_payload("online"),
            qos=1,
            retain=True,
        )

        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            logger.error(
                "Failed to publish online status: %s",
                result.rc,
            )
            return

        logger.info(
            "Published online status to: %s",
            self.status_topic,
        )

    def _get_status_payload(self, status):

        payload = {
            "group": GROUP,
            "status": status,
            "mac": self.mac,
            "hostname": TOTAM_HOSTNAME,
        }

        return json.dumps(payload)

    # =========================================================
    # CONNECTION
    # =========================================================

    def _connect(self):

        logger.info(
            "Connecting to MQTT %s:%s",
            MQTT_BROKER,
            MQTT_PORT,
        )

        self.client.connect(
            MQTT_BROKER,
            MQTT_PORT,
        )

    def start(self):

        logger.info("Starting MQTT client")

        retries = 0

        while True:
            try:
                self._connection_error = None

                # Inicia uma tentativa de conexão.
                self._connect()

                # Aguarda a resposta do broker.
                deadline = time.monotonic() + 10

                while (
                    not self.client.is_connected()
                    and self._connection_error is None
                ):
                    result = self.client.loop(timeout=1.0)

                    if result != mqtt.MQTT_ERR_SUCCESS:
                        raise ConnectionError(
                            f"MQTT loop failed: "
                            f"{mqtt.error_string(result)}"
                        )

                    if time.monotonic() >= deadline:
                        raise TimeoutError(
                            "MQTT connection timed out"
                        )

                # O broker recusou a autenticação.
                if self._connection_error is not None:
                    raise ConnectionError(
                        f"MQTT connection rejected: "
                        f"{self._connection_error}"
                    )

                # Só zera o contador após conectar de verdade.
                retries = 0

                logger.info("MQTT session established")

                # Mantém o cliente processando mensagens.
                while self.client.is_connected():

                    result = self.client.loop(timeout=1.0)

                    if result != mqtt.MQTT_ERR_SUCCESS:
                        raise ConnectionError(
                            f"MQTT loop failed: "
                            f"{mqtt.error_string(result)}"
                        )

                raise ConnectionError("MQTT connection lost")

            except KeyboardInterrupt:
                logger.info("MQTT client stopped manually")
                self.disconnect()
                raise

            except Exception as exc:

                try:
                    self.client.disconnect()
                except Exception:
                    pass

                # Limite atingido: encerra a aplicação.
                if retries >= MQTT_MAX_RETRIES:
                    logger.critical(
                        "Maximum MQTT retries reached (%s). "
                        "Terminating application. Last error: %s",
                        MQTT_MAX_RETRIES,
                        exc,
                        exc_info=True,
                    )
                    raise

                delay = min(
                    MQTT_RETRY_INITIAL_DELAY * (2 ** retries),
                    MQTT_RETRY_MAX_DELAY,
                )

                retries += 1

                logger.warning(
                    "MQTT attempt failed. "
                    "Retry %s/%s in %s seconds. Error: %s",
                    retries,
                    MQTT_MAX_RETRIES,
                    delay,
                    exc,
                )

                time.sleep(delay)

    def disconnect(self):

        logger.info("Disconnecting MQTT")

        try:
            self.client.disconnect()

        except Exception:
            logger.exception(
                "Error disconnecting MQTT"
            )

    # =========================================================
    # UTILS
    # =========================================================

    @staticmethod
    def _get_mac():

        mac = uuid.getnode()

        return ":".join(
            f"{(mac >> ele) & 0xff:02x}"
            for ele in range(40, -1, -8)
        )