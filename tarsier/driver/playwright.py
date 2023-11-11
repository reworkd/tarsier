from playwright.async_api import Page as PageAsync
from playwright.sync_api import Page as PageSync

from tarsier.driver._base import BrowserDriver


class PlaywrightSyncDriver(BrowserDriver):
    def __init__(self, page: PageSync):
        self.page = page

    async def run_js(self, js: str):
        return self.page.evaluate(js)

    async def take_screenshot(self) -> bytes:
        return self.page.screenshot(type="png")

    async def set_viewport_size(self, width, height):
        self.page.set_viewport_size({"width": width, "height": height})


class PlaywrightAsyncDriver(BrowserDriver):
    def __init__(self, page: PageAsync):
        self.page = page

    async def run_js(self, js: str):
        result = await self.page.evaluate(js)
        return result

    async def take_screenshot(self) -> bytes:
        return await self.page.screenshot(type="png")

    async def set_viewport_size(self, width, height):
        await self.page.set_viewport_size({"width": width, "height": height})
