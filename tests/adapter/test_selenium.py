import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from tarsier.adapter import SeleniumAdapter


@pytest.mark.asyncio
async def test_get_viewport_size_returns_correct_values(chrome_driver: WebDriver):
    adapter = SeleniumAdapter(chrome_driver)

    await adapter.set_viewport_size(1920, 1080)
    viewport = await adapter.get_viewport_size()

    assert viewport["width"] == 1920
    assert viewport["height"] == 1080
    assert viewport["content_height"] == 1080
