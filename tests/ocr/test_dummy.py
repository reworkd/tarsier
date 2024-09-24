import pytest
from playwright.async_api import Page as AsyncPage

from tarsier import Tarsier
from tarsier.ocr.ocr_service import DummyOCRService


@pytest.mark.asyncio
async def test_dummy_ocr_returns_no_text(async_page: AsyncPage):
    tarsier = Tarsier(DummyOCRService())

    await async_page.goto("https://news.ycombinator.com/")

    text, paths = await tarsier.page_to_text(async_page)
    lines = text.split("\n")
    divider_lines = [lines[0], lines[2]]

    # Test page text is empty
    assert len(lines) == 3
    assert lines[1] == ""
    assert all([line == "-" * len(line) for line in divider_lines])

    # Test paths exist
    assert isinstance(paths[0].tarsierID, int)
    assert isinstance(paths[0].xpath, str)
    hacker_news_el = await async_page.query_selector(paths[1].xpath)
    assert "Hacker" in await hacker_news_el.inner_text()
