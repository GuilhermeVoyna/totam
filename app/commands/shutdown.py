import logging

from app.commands.command import Command

logger = logging.getLogger(__name__)


class ShutdownCommand(Command):

    def __init__(self, system):
        self.system = system

    def execute(self):

        logger.warning("Executing SHUTDOWN")

        self.system.shutdown()