import os
import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "html_file, expected_xpath",
    [
        ("mock_html/namespace.html", "//html/body/*[name()=\"sc:visitoridentification\"]/div"),
    ],
)
async def test_xpath(tarsier, async_page, html_file, expected_xpath):

    html_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), html_file))
    await async_page.goto(f"file://{html_file_path}")

    page_text, tag_to_xpath = await tarsier.page_to_text(
        async_page, tag_text_elements=True
    )
    assert tag_to_xpath[0] == expected_xpath, (
        f"tag_to_xpath does not match expected xpath for "
        f"{html_file}. Got: {tag_to_xpath}"
    )
