import platform

from .linux import LinuxSystem
from .windows import WindowsSystem


def create_system():

    operating_system = platform.system()

    if operating_system == "Linux":
        return LinuxSystem()

    if operating_system == "Windows":
        return WindowsSystem()

    raise RuntimeError(
        f"Unsupported operating system: {operating_system}"
    )