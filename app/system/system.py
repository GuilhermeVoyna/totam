from abc import ABC, abstractmethod
from app.config.settings import TOTAM_MAC

class System(ABC):

    @abstractmethod
    def reboot(self):
        pass

    @abstractmethod
    def shutdown(self):
        pass

    @abstractmethod
    def suspend(self):
        pass

    def get_mac(self) -> str:
        return TOTAM_MAC