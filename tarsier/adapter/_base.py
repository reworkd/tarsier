from abc import ABC, abstractmethod
from typing import Any

from tarsier.adapter.types import ViewPortSize


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

    @abstractmethod
    async def get_viewport_size(self) -> ViewPortSize:
        pass
