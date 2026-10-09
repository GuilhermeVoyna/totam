import logging
import time

import paho.mqtt.client as mqtt

from app.config.settings import (
    MQTT_BROKER,
    MQTT_PORT,
    MQTT_MAX_RETRIES,
    MQTT_RETRY_INITIAL_DELAY,
    MQTT_RETRY_MAX_DELAY,
    HEARTBEAT_INTERVAL,
)


logger = logging.getLogger(__name__)


class MQTTConnection:

    CONNECT_TIMEOUT = 10
    LOOP_TIMEOUT = 1.0

    def __init__(
        self,
        client,
        callbacks,
        publisher,
    ):
        self.client = client
        self.callbacks = callbacks
        self.publisher = publisher
        self.stopping = False

    def start(self):
        logger.info("Starting MQTT connection manager")

        retries = 0

        while not self.stopping:
            try:
                self._connect_and_wait()

                # Reinicia o contador após conectar com sucesso.
                retries = 0

                self._run_connected_session()

            except KeyboardInterrupt:
                logger.info("MQTT connection stopped manually")
                self.disconnect()
                raise

            except Exception as exc:
                if self.stopping:
                    break

                self._disconnect_transport()

                if retries >= MQTT_MAX_RETRIES:
                    logger.critical(
                        "Maximum MQTT retries reached (%s). "
                        "Last error: %s",
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
                    "MQTT failed. Retry %s/%s in %s seconds: %s",
                    retries,
                    MQTT_MAX_RETRIES,
                    delay,
                    exc,
                )

                time.sleep(delay)

    def _connect_and_wait(self):
        self.callbacks.connection_error = None

        logger.info(
            "Connecting to MQTT %s:%s",
            MQTT_BROKER,
            MQTT_PORT,
        )

        self.client.connect(
            MQTT_BROKER,
            MQTT_PORT,
        )

        deadline = time.monotonic() + self.CONNECT_TIMEOUT

        while (
            not self.client.is_connected()
            and self.callbacks.connection_error is None
        ):
            remaining = deadline - time.monotonic()

            if remaining <= 0:
                raise TimeoutError(
                    "MQTT connection timed out"
                )

            result = self.client.loop(
                timeout=min(self.LOOP_TIMEOUT, remaining)
            )

            if self.callbacks.connection_error is not None:
                raise ConnectionError(
                    "MQTT connection rejected: "
                    f"{self.callbacks.connection_error}"
                )

            if result != mqtt.MQTT_ERR_SUCCESS:
                raise ConnectionError(
                    f"MQTT loop failed: "
                    f"{mqtt.error_string(result)}"
                )

        if self.callbacks.connection_error is not None:
            raise ConnectionError(
                "MQTT connection rejected: "
                f"{self.callbacks.connection_error}"
            )

        if not self.client.is_connected():
            raise ConnectionError(
                "MQTT connection was not established"
            )

    def _run_connected_session(self):
        logger.info("MQTT session established")

        next_heartbeat = (
            time.monotonic() + HEARTBEAT_INTERVAL
            if HEARTBEAT_INTERVAL > 0
            else None
        )

        if next_heartbeat is None:
            logger.info("Heartbeat disabled")

        while self.client.is_connected() and not self.stopping:
            result = self.client.loop(
                timeout=self.LOOP_TIMEOUT
            )

            if result != mqtt.MQTT_ERR_SUCCESS:
                raise ConnectionError(
                    f"MQTT loop failed: "
                    f"{mqtt.error_string(result)}"
                )

            if (
                next_heartbeat is not None
                and time.monotonic() >= next_heartbeat
            ):
                self.publisher.publish_heartbeat()

                next_heartbeat = (
                    time.monotonic() + HEARTBEAT_INTERVAL
                )

        if not self.stopping:
            raise ConnectionError(
                "MQTT connection lost"
            )

    def _disconnect_transport(self):
        try:
            self.client.disconnect()
        except Exception:
            logger.debug(
                "Error closing MQTT transport",
                exc_info=True,
            )

    def disconnect(self):
        self.stopping = True

        logger.info("Stopping MQTT connection")

        try:
            if self.client.is_connected():
                self.publisher.publish_status("offline")

            self.client.disconnect()

        except Exception:
            logger.exception(
                "Error disconnecting MQTT",
            )