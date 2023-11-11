from asyncio import Protocol
from typing import Dict, Tuple

from tarsier.driver import AnyDriver, BrowserDriver, driver_factory


class ITarsier(Protocol):
    async def page_to_image(
        self, driver: BrowserDriver
    ) -> Tuple[bytes, Dict[int, str]]:
        raise NotImplementedError()

    async def page_to_text(self, driver: BrowserDriver) -> Tuple[str, Dict[int, str]]:
        raise NotImplementedError()

    @staticmethod
    def create_driver(driver: AnyDriver) -> BrowserDriver:
        return driver_factory(driver)
