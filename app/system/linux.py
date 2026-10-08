import subprocess

from .system import System


class LinuxSystem(System):

    def reboot(self):
        subprocess.run(
            ["shutdown", "-r", "now"],
            timeout=10,
            check=True,
        )

    def shutdown(self):
        subprocess.run(
            ["shutdown", "-h", "now"],
            timeout=10,
            check=True,
        )

    def suspend(self):
        subprocess.run(
            ["systemctl", "suspend"],
            timeout=10,
            check=True,
        )