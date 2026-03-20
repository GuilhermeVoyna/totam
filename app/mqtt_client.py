import os
import ssl
import json
import socket
import logging
import uuid

import paho.mqtt.client as mqtt
from dotenv import load_dotenv

from commands import process_command

load_dotenv()

logger = logging.getLogger(__name__)

# =========================
# CONFIG
# =========================

MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
MQTT_BROKER   = os.getenv("MQTT_BROKER")
MQTT_PORT     = int(os.getenv("MQTT_PORT", 8883))

GROUP    = os.getenv("GROUP")
HOSTNAME = os.getenv("HOSTNAME") or socket.gethostname()

COMMAND_TOPIC   = f"pc/{HOSTNAME}/command"
BROADCAST_TOPIC = "pc/all/command"
STATUS_TOPIC    = f"pc/{HOSTNAME}/status"

# =========================
# UTILS
# =========================

def get_mac():
    mac = uuid.getnode()
    return ':'.join(f"{(mac >> ele) & 0xff:02x}" for ele in range(40, -1, -8))


def get_status_payload(status):
    payload = {
        "group": GROUP,
        "status": status,
        "mac": get_mac(),
        "hostname": HOSTNAME
    }
    return json.dumps(payload)

# =========================
# MQTT CALLBACKS
# =========================

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        logger.info("MQTT connected")

        client.subscribe(COMMAND_TOPIC, qos=1)
        client.subscribe(BROADCAST_TOPIC, qos=1)

        logger.info("Subscribed to: %s", COMMAND_TOPIC)
        logger.info("Subscribed to: %s", BROADCAST_TOPIC)

        client.publish(
            STATUS_TOPIC,
            get_status_payload("online"),
            qos=1,
            retain=True
        )
    else:
        logger.error("MQTT connection failed: %s", rc)


def on_disconnect(client, userdata, rc, properties=None):
    logger.warning("Disconnected from MQTT (rc=%s)", rc)


def on_message(client, userdata, msg):
    payload = msg.payload.decode("utf-8")

    logger.info("Message | %s | %s", msg.topic, payload)

    if msg.topic in [COMMAND_TOPIC, BROADCAST_TOPIC]:
        process_command(payload)

# =========================
# START
# =========================

def start():
    logger.info("Starting MQTT client")
    logger.info("Hostname: %s", HOSTNAME)

    client = mqtt.Client(
        client_id=f"{HOSTNAME}-{get_mac()}",
        protocol=mqtt.MQTTv5
    )

    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.tls_set(tls_version=ssl.PROTOCOL_TLS)

    # Last Will
    client.will_set(
        STATUS_TOPIC,
        get_status_payload("offline"),
        qos=1,
        retain=True
    )

    # Callbacks
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    client.reconnect_delay_set(min_delay=2, max_delay=30)

    # Connect
    logger.info("Connecting to %s:%s", MQTT_BROKER, MQTT_PORT)
    client.connect(MQTT_BROKER, MQTT_PORT)

    client.loop_forever()