import time
import socket
import paho.mqtt.client as mqtt
import ssl
import os
import subprocess
import uuid
from dotenv import load_dotenv
import logging
import json

load_dotenv()


# =========================
# CONFIG
# =========================

logging.basicConfig(
    level=logging.DEBUG, 
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
MQTT_BROKER   = os.getenv("MQTT_BROKER")
MQTT_PORT     = int(os.getenv("MQTT_PORT"))

SHUTDOWN = os.getenv("SHUTDOWN")
REBOOT   = os.getenv("REBOOT")
SLEEP    = os.getenv("SLEEP")

HOSTNAME = os.getenv("HOSTNAME") or socket.gethostname()

COMMAND_TOPIC = f"pc/{HOSTNAME}/command"
BROADCAST_TOPIC = "pc/all/command"
STATUS_TOPIC = f"pc/{HOSTNAME}/status"

def get_mac():
    mac = uuid.getnode()
    mac_str = ':'.join(f"{(mac >> ele) & 0xff:02x}" for ele in range(40, -1, -8))
    return mac_str


def get_status_payload(status):
    mac = get_mac()
    payload = {
    "status": status,
    "mac": mac,
    "hostname": HOSTNAME 
    }
    logger.debug("Payload JSON: %s", payload)
    return json.dumps(payload)

LAST_WILL_MESSAGE = get_status_payload("offline")

# =========================
# NETWORK CHECK
# =========================

def network_ok():
    try:
        socket.gethostbyname(MQTT_BROKER)
        with socket.create_connection((MQTT_BROKER, MQTT_PORT), timeout=3):
            return True
    except OSError:
        return False


def wait_network():
    logger.info("Waiting network...")

    while not network_ok():
        logger.error("Network not ready, retrying...")
        time.sleep(3)
    logger.info("Network OK")

# =========================
# COMMAND PROCESS
# =========================
def shutdown():
    logger.info("Shutting down PC")
    subprocess.run(["shutdown", "-h", "now"])

def reboot():
    logger.info("Rebooting PC")
    subprocess.run(["shutdown", "-r", "now"])

def sleep():
    logger.info("Suspending PC")
    subprocess.run(["systemctl","suspend"])

actions = {
    SHUTDOWN: shutdown(),
    REBOOT: reboot(),
    SLEEP: sleep()
}

def process_command(command):
    command = command.lower()
    logger.info(f"Command received: {command}")
    action = actions.get(command)

    if action:
        action()
    else:
        logger.warning("Unknown command: %s", command)

# =========================
# MQTT CALLBACKS
# =========================

def on_connect(client, userdata, flags, rc, properties=None): 
    logger.info("MQTT Connected: %s", rc)
    if rc == 0: 
        logger.info("Subscribing topics...") 
        client.subscribe(COMMAND_TOPIC) 
        client.subscribe(BROADCAST_TOPIC) 
        logger.info("Subscribed to: %s", COMMAND_TOPIC)
        logger.info("Subscribed to: %s", BROADCAST_TOPIC)
        
        client.publish(STATUS_TOPIC, get_status_payload("online"), retain=True) 
    else:
        logger.error("MQTT connection failed with return code: %s", rc)

def on_disconnect(client, userdata, *args, **kwargs):
    logger.warning("=== on_disconnect ===")
    logger.warning("userdata: %s", userdata)
    logger.warning("args (positional arguments): %s", args)
    logger.warning("kwargs (keyword arguments): %s", kwargs)
    logger.warning("=====================")

def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode("utf-8")

    logger.info(f"Message received | Topic: {topic} | Payload: {payload}")

    if topic in [COMMAND_TOPIC, BROADCAST_TOPIC]:
        process_command(payload)

# =========================
# START
# =========================

logger.info("Starting TOTAM MQTT Controller")
logger.info("Hostname: %s", HOSTNAME)

wait_network()

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

client.tls_set(tls_version=ssl.PROTOCOL_TLS)

# Last will
client.will_set(STATUS_TOPIC, LAST_WILL_MESSAGE, retain=True)

client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message

client.reconnect_delay_set(min_delay=2, max_delay=30)

# =========================
# CONNECT LOOP
# =========================

while True:
    try:
        logger.info("Connecting to MQTT...")
        logger.debug("Connecting to %s:%s", MQTT_BROKER, MQTT_PORT)
        client.connect(MQTT_BROKER, MQTT_PORT)
        break
    except Exception as e:
        logger.error("MQTT connection failed:", e)
        time.sleep(5)

client.loop_start()

# =========================
# WATCHDOG
# =========================

while True:
    
    if not network_ok():
        logger.error("Network lost, waiting...")
        wait_network()

    if not client.is_connected():
        try:
            logger.warning("Reconnecting MQTT...")
            client.reconnect()
        except Exception as e:
            logger.error("Reconnect error:", e)


    time.sleep(5)