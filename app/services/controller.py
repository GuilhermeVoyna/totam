import logging

from app.commands import (
    RebootCommand,
    ShutdownCommand,
    SuspendCommand
)

logger = logging.getLogger(__name__)


class Controller:

    def __init__(self, system):

        self.commands = {
            "reboot": RebootCommand(system),
            "shutdown": ShutdownCommand(system),
            "sleep": SuspendCommand(system),
        }

    def process_command(self, payload):

        command_name = payload.strip().lower()

        logger.info(
            "Command received: %s",
            command_name
        )

        command = self.commands.get(command_name)

        if command is None:
            logger.warning(
                "Unknown command: %s",
                command_name
            )
            return

        try:
            command.execute()

        except Exception:
            logger.exception(
                "Error executing command '%s'",
                command_name
            )