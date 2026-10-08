import logging

from app.commands.command import Command

logger = logging.getLogger(__name__)


class RebootCommand(Command):

    def __init__(self, system):
        self.system = system

    def execute(self):

        logger.warning("Executing REBOOT")
        
        self.system.reboot()