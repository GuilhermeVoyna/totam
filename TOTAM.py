import time
import socket
import paho.mqtt.client as mqtt
import ssl
import os
import subprocess


# =========================
# CONFIG
# =========================

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
    print("Waiting network...")

    while not network_ok():
        print("Network not ready, retrying...")
        time.sleep(3)
    print("Network OK")

# =========================
# COMMAND PROCESS
# =========================

def process_command(command):
    command = command.lower()
    print(f"Command received: {command}")

    if command == SHUTDOWN:
        print("Shutting down PC")
        subprocess.run(["sudo", "shutdown", "-h", "now"])

    elif command == REBOOT:
        print("Rebooting PC")
        subprocess.run(["sudo", "shutdown", "-r", "now"])

    elif command == SLEEP:
        print("Suspending PC")
        subprocess.run(["sudo", "systemctl","suspend"])

    else:
        print("Unknown command:", command)

# =========================
# MQTT CALLBACKS
# =========================

def on_connect(client, userdata, flags, rc, properties=None): 
    print("MQTT Connected:", rc) 
    if rc == 0: 
        print("Subscribing topics...") 
        client.subscribe(COMMAND_TOPIC) 
        client.subscribe(BROADCAST_TOPIC) 
        print("Subscribed to:", COMMAND_TOPIC) 
        print("Subscribed to:", BROADCAST_TOPIC)
        client.publish(STATUS_TOPIC, "online", retain=True) 
    else: print("MQTT connection failed")

def on_disconnect(client, userdata, *args, **kwargs):
    print("=== on_disconnect ===")
    print("userdata:", userdata)
    print("args (positional arguments):", args)
    print("kwargs (keyword arguments):", kwargs)
    print("=====================")
    
def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode("utf-8")

    print(f"Message received | Topic: {topic} | Payload: {payload}")

    if topic in [COMMAND_TOPIC, BROADCAST_TOPIC]:
        process_command(payload)

# =========================
# START
# =========================

print("Starting TOTAM MQTT Controller")
print("Hostname:", HOSTNAME)

wait_network()

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

client.tls_set(tls_version=ssl.PROTOCOL_TLS)

# Last will
client.will_set(STATUS_TOPIC, "offline", retain=True)

client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message

client.reconnect_delay_set(min_delay=2, max_delay=30)

# =========================
# CONNECT LOOP
# =========================

while True:
    try:
        print("Connecting to MQTT...")
        client.connect(MQTT_BROKER, MQTT_PORT)
        break
    except Exception as e:
        print("MQTT connection failed:", e)
        time.sleep(5)

client.loop_start()

# =========================
# WATCHDOG
# =========================

while True:

    if not network_ok():
        print("Network lost, waiting...")
        wait_network()

    if not client.is_connected():
        try:
            print("Reconnecting MQTT...")
            client.reconnect()
        except Exception as e:
            print("Reconnect error:", e)


    time.sleep(5)