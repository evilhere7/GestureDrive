from abc import ABC, abstractmethod
from app.controls import ControlState

class BaseInputAdapter(ABC):
    """Abstract Base Class for input adapters (Keyboard, Virtual Gamepad, Simulation)."""

    @abstractmethod
    def update(self, state: ControlState) -> None:
        """Send hardware or virtual driver events based on current control state."""
        pass

    @abstractmethod
    def release_all(self) -> None:
        """Immediately release all keys/buttons/axes."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if adapter dependencies and drivers are available."""
        pass
