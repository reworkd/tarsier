from typing import Any

from playwright.async_api import Page as PageAsync
from playwright.sync_api import Page as PageSync

from tarsier.adapter._base import BrowserAdapter


class PlaywrightSyncAdapter(BrowserAdapter):
    def __init__(self, page: PageSync):
        self._page = page
        raise NotImplementedError(
            "Sync playwright is not yet supported. Please use the PlaywrightAsyncDriver instead."
        )

    async def run_js(self, js: str) -> Any:
        return self._page.evaluate(js)

    async def take_screenshot(self) -> bytes:
        return self._page.screenshot(type="png")

    async def set_viewport_size(self, width: int, height: int) -> None:
        self._page.set_viewport_size({"width": width, "height": height})


class PlaywrightAsyncAdapter(BrowserAdapter):
    def __init__(self, page: PageAsync):
        self._page = page

    async def run_js(self, js: str) -> Any:
        return await self._page.evaluate(js)

    async def take_screenshot(self) -> bytes:
        return await self._page.screenshot(type="png")

    async def set_viewport_size(self, width: int, height: int) -> None:
        await self._page.set_viewport_size({"width": width, "height": height})
