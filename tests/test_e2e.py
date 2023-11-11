import pytest
from playwright.async_api import Page as AsyncPage

from tarsier import Tarsier


@pytest.mark.asyncio
async def test_async_playwright(async_page: AsyncPage, tarsier: Tarsier) -> None:
    await async_page.goto("https://news.ycombinator.com/")

    driver = tarsier.create_driver(async_page)
    text, paths = await tarsier.page_to_text(driver)

    assert "Hacker" in text and "News" in text
    assert paths

    assert type(list(paths.keys())[0]) is int
    assert type(list(paths.values())[0]) is str

    hacker_news_el = await async_page.query_selector(paths[1])
    assert "Hacker" in await hacker_news_el.inner_text()

