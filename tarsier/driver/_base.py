from abc import ABC, abstractmethod


class BrowserDriver(ABC):
    @abstractmethod
    async def run_js(self, js: str):
        pass

    @abstractmethod
    async def take_screenshot(self) -> bytes:
        pass

    @abstractmethod
    async def set_viewport_size(self, width: int, height: int):
        pass
