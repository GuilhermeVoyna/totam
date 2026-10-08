import subprocess

from .system import System


class WindowsSystem(System):

    def reboot(self):
        subprocess.run(
            ["shutdown", "/r", "/t", "0"],
            timeout=10,
            check=True,
        )

    def shutdown(self):
        subprocess.run(
            ["shutdown", "/s", "/t", "0"],
            timeout=10,
            check=True,
        )

    def suspend(self):
        subprocess.run(
            [
                "powershell",
                "-Command",
                "Add-Type -AssemblyName System.Windows.Forms"
            ],
            timeout=10,
            check=True,
        )