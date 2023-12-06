import io
from typing import Any

from PIL import Image
from playwright.async_api import Page as PageAsync
from playwright.sync_api import Page as PageSync

from tarsier.adapter._base import BrowserAdapter
from tarsier.adapter.image_utils import stitch_screenshots_in_memory
from tarsier.adapter.types import ViewPortSize


class PlaywrightSyncAdapter(BrowserAdapter):
    STRIP_RETURN = "return window."

    def __init__(self, page: PageSync):
        self._page = page
        raise NotImplementedError(
            "Sync playwright is not yet supported. Please use the PlaywrightAsyncDriver instead."
        )

    async def run_js(self, js: str) -> Any:
        if js.startswith(self.STRIP_RETURN):
            js = js[len(self.STRIP_RETURN) :]

        return self._page.evaluate(js)

    async def take_screenshot(self) -> bytes:
        return self._page.screenshot(type="png")

    async def set_viewport_size(self, width: int, height: int) -> None:
        self._page.set_viewport_size({"width": width, "height": height})

    async def get_viewport_size(self) -> ViewPortSize:
        width, height, scroll_height = await self.run_js(
            "[window.innerWidth, window.innerHeight, document.documentElement.scrollHeight]"
        )

        return {"width": width, "height": height, "content_height": scroll_height}


class PlaywrightAsyncAdapter(BrowserAdapter):
    STRIP_RETURN = "return window."

    def __init__(self, page: PageAsync):
        self._page = page

    async def run_js(self, js: str) -> Any:
        if js.startswith(self.STRIP_RETURN):
            js = js[len(self.STRIP_RETURN) :]

        return await self._page.evaluate(js)

    async def take_screenshot(self) -> bytes:
        """
        Take a screenshot of the whole page via scrolling and stitching together multiple screenshots
        """
        viewport_height = self._page.viewport_size["height"]
        total_height = await self._page.evaluate("document.body.scrollHeight")
        current_height = 0

        images = []
        while current_height < total_height:
            screenshot_bytes = await self._page.screenshot()
            images.append(Image.open(io.BytesIO(screenshot_bytes)))

            await self._page.mouse.wheel(0, viewport_height)
            await self._page.wait_for_timeout(500)  # Wait for scrolling to finish
            current_height += viewport_height

        return stitch_screenshots_in_memory(images)

    async def set_viewport_size(self, width: int, height: int) -> None:
        await self._page.set_viewport_size({"width": width, "height": height})

    async def get_viewport_size(self) -> ViewPortSize:
        width, height, scroll_height = await self.run_js(
            "[window.innerWidth, window.innerHeight, document.documentElement.scrollHeight]"
        )

        return {"width": width, "height": height, "content_height": scroll_height}
