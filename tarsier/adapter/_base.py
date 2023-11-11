from abc import ABC, abstractmethod
from typing import Any


class BrowserAdapter(ABC):
    @abstractmethod
    async def run_js(self, js: str) -> Any:
        pass

    @abstractmethod
    async def take_screenshot(self) -> bytes:
        pass

    @abstractmethod
    async def set_viewport_size(self, width: int, height: int) -> None:
        pass
