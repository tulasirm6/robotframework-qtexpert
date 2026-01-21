from abc import ABC, abstractmethod

class BaseBackend(ABC):
    @abstractmethod
    def connect(self, *args, **kwargs): pass
    @abstractmethod
    def disconnect(self): pass
    @abstractmethod
    def find_element(self, locator, **kwargs): pass
    @abstractmethod
    def click(self, element): pass
    @abstractmethod
    def get_value(self, element): pass
    @abstractmethod
    def set_value(self, element, value): pass
    @abstractmethod
    def close_app(self): pass