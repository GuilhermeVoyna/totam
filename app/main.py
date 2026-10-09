import logging
import sys

from app.mqtt.client import MQTTClient
from app.services.controller import Controller
from app.system.factory import create_system


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stdout,
    )


def main():
    setup_logging()

    logger = logging.getLogger("main")
    logger.info("Starting TOTAM service...")

    try:
        # Descobre e cria a implementação do sistema operacional
        system = create_system()

        # Cria o controller responsável pelos Commands
        controller = Controller(
            system=system
        )

        # Inicia o cliente MQTT
        mqtt_client = MQTTClient(controller=controller, mac=system.get_mac())
        mqtt_client.start()

    except KeyboardInterrupt:
        logger.info("Service stopped manually")

    except Exception as e:
        logger.exception("Fatal error: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()