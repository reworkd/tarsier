import pytest
from playwright.async_api import Page

from tarsier.adapter import PlaywrightAsyncAdapter, PlaywrightSyncAdapter


def test_sync_playwright_fails(mocker):
    with pytest.raises(NotImplementedError):
        PlaywrightSyncAdapter(mocker.Mock())


@pytest.mark.asyncio
async def test_run_js(mocker):
    mock_page = mocker.MagicMock(spec=Page)
    driver = PlaywrightAsyncAdapter(mock_page)

    # Test run_js
    js_script = "return true;"
    await driver.run_js(js_script)
    mock_page.evaluate.assert_called_once_with(js_script)


@pytest.mark.asyncio
async def test_take_screenshot(mocker):
    mock_page = mocker.MagicMock(spec=Page)
    driver = PlaywrightAsyncAdapter(mock_page)

    # Test take_screenshot
    await driver.take_screenshot()
    mock_page.screenshot.assert_called_once_with(type="png", full_page=True)


@pytest.mark.asyncio
async def test_set_viewport_size(mocker):
    mock_page = mocker.MagicMock(spec=Page)
    driver = PlaywrightAsyncAdapter(mock_page)

    # Test set_viewport_size
    width, height = 1920, 1080
    await driver.set_viewport_size(width, height)
    mock_page.set_viewport_size.assert_called_once_with(
        {"width": width, "height": height}
    )


@pytest.mark.asyncio
async def test_get_viewport_size_returns_correct_values(async_page: Page):
    adapter = PlaywrightAsyncAdapter(async_page)

    await adapter.set_viewport_size(1920, 1080)
    viewport = await adapter.get_viewport_size()

    assert viewport["width"] == 1920
    assert viewport["height"] == 1080
    assert viewport["content_height"] == 1080
