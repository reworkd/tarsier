import pytest
from playwright.async_api import Page

from tarsier.driver import PlaywrightSyncDriver, PlaywrightAsyncDriver


def test_sync_playwright_fails(mocker):
    with pytest.raises(NotImplementedError):
        PlaywrightSyncDriver(mocker.Mock())


@pytest.mark.asyncio
async def test_run_js(mocker):
    mock_page = mocker.MagicMock(spec=Page)
    driver = PlaywrightAsyncDriver(mock_page)

    # Test run_js
    js_script = "return true;"
    await driver.run_js(js_script)
    mock_page.evaluate.assert_called_once_with(js_script)


@pytest.mark.asyncio
async def test_take_screenshot(mocker):
    mock_page = mocker.MagicMock(spec=Page)
    driver = PlaywrightAsyncDriver(mock_page)

    # Test take_screenshot
    await driver.take_screenshot()
    mock_page.screenshot.assert_called_once_with(type="png")


@pytest.mark.asyncio
async def test_set_viewport_size(mocker):
    mock_page = mocker.MagicMock(spec=Page)
    driver = PlaywrightAsyncDriver(mock_page)

    # Test set_viewport_size
    width, height = 1920, 1080
    await driver.set_viewport_size(width, height)
    mock_page.set_viewport_size.assert_called_once_with(
        {"width": width, "height": height}
    )
