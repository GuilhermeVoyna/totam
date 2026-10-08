import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[2]

load_dotenv(BASE_DIR / ".env")

MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
MQTT_BROKER = os.getenv("MQTT_BROKER")
MQTT_PORT = int(os.getenv("MQTT_PORT", "8883"))

TOTAM_HOSTNAME = os.getenv("TOTAM_HOSTNAME")
GROUP = os.getenv("GROUP")

MQTT_MAX_RETRIES = int(os.getenv("MQTT_MAX_RETRIES", "5"))
MQTT_RETRY_INITIAL_DELAY = int(os.getenv("MQTT_RETRY_INITIAL_DELAY", "1"))
MQTT_RETRY_MAX_DELAY = int(os.getenv("MQTT_RETRY_MAX_DELAY", "16"))