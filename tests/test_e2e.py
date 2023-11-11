import pytest
from playwright.async_api import Page as AsyncPage
from playwright.sync_api import Page
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By

from tarsier import Tarsier


# noinspection DuplicatedCode
@pytest.mark.skipif(reason="Sync Playwright is not yet supported")
def test_sync_playwright(sync_page: Page, tarsier: Tarsier):
    text, paths = tarsier.page_to_text(sync_page)

    assert "Hacker" in text and "News" in text
    assert paths

    assert type(list(paths.keys())[0]) is int
    assert type(list(paths.values())[0]) is str

    hacker_news_el = sync_page.query_selector(paths[1])
    assert "Hacker" in hacker_news_el.inner_text()


# noinspection DuplicatedCode
@pytest.mark.asyncio
async def test_async_playwright(async_page: AsyncPage, tarsier: Tarsier) -> None:
    await async_page.goto("https://news.ycombinator.com/")

    text, paths = await tarsier.page_to_text(async_page)

    assert "Hacker" in text and "News" in text
    assert paths

    assert type(list(paths.keys())[0]) is int
    assert type(list(paths.values())[0]) is str

    hacker_news_el = await async_page.query_selector(paths[1])
    assert "Hacker" in await hacker_news_el.inner_text()


# noinspection DuplicatedCode
@pytest.mark.asyncio
async def test_selenium(chrome_driver: WebDriver, tarsier: Tarsier):
    chrome_driver.get("https://news.ycombinator.com/")

    text, paths = await tarsier.page_to_text(chrome_driver)

    assert "Hacker" in text and "News" in text
    assert paths

    assert type(list(paths.keys())[0]) is int
    assert type(list(paths.values())[0]) is str

    hacker_news_el = chrome_driver.find_element(By.XPATH, paths[1])
    assert "Hacker" in hacker_news_el.text
