import logging
import subprocess
import json
import os

logger = logging.getLogger(__name__)

# =========================
# CONFIG
# =========================

SHUTDOWN = os.getenv("SHUTDOWN", "shutdown")
REBOOT   = os.getenv("REBOOT", "reboot")
SLEEP    = os.getenv("SLEEP", "sleep")
UPDATE   = os.getenv("UPDATE", "update")
GROUP    = os.getenv("GROUP")
REPO_PATH = os.getenv("REPO_PATH")

# =========================
# ACTIONS
# =========================

def shutdown():
    logger.warning("Executing SHUTDOWN")
    subprocess.run(["shutdown", "-h", "now"], timeout=10)


def reboot():
    logger.warning("Executing REBOOT")
    subprocess.run(["shutdown", "-r", "now"], timeout=10)


def sleep():
    logger.warning("Executing SLEEP")
    subprocess.run(["systemctl", "suspend"], timeout=10)


def update():
    logger.warning("Executing FULL UPDATE via install.sh")

    if not REPO_PATH:
        logger.error("REPO_PATH not set")
        return

    install_script = os.path.join(REPO_PATH, "install.sh")

    if not os.path.exists(install_script):
        logger.error("install.sh not found at %s", install_script)
        return

    try:
        subprocess.run(
            ["bash", install_script],
            timeout=120,
            check=True
        )

    except Exception as e:
        logger.error("Update failed: %s", e)

# =========================
# ACTION MAP
# =========================

actions = {
    SHUTDOWN: shutdown,
    REBOOT: reboot,
    SLEEP: sleep,
    UPDATE: update
}

# =========================
# PROCESS COMMAND
# =========================

def process_command(payload):

    command=payload

    command = command.strip().lower()

    logger.info("Command received: %s", command)

    action = actions.get(command)

    if not action:
        logger.warning("Unknown command: %s", command)
        return

    try:
        action()
    except Exception as e:
        logger.exception("Error executing command '%s': %s", command, e)