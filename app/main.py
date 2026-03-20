import logging
import sys

from mqtt_client import start


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stdout
    )


def main():
    setup_logging()

    logger = logging.getLogger("main")
    logger.info("Starting TOTAM service...")

    try:
        start()
    except KeyboardInterrupt:
        logger.info("Service stopped manually")
    except Exception as e:
        logger.exception("Fatal error: %s", e)
        sys.exit(1)  # importante pro systemd reiniciar


if __name__ == "__main__":
    main()