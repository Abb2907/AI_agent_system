from abc import ABC, abstractmethod


class BaseTool(ABC):
    """Abstract base class for all agent tools."""

    name: str
    description: str

    @abstractmethod
    def execute(self, input_data: str) -> str:
        """Execute the tool with the given input and return a result string."""
        ...
