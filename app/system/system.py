from abc import ABC, abstractmethod


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