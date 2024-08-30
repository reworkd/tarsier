import os
import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "html_file, expected_text_content",
    [
        ("small.html", ["Small"]),
        ("medium.html", ["Medium"]),
        ("large.html", ["**Large**"]),
        ("x_large.html", ["**XLarge**"]),
        ("xx_large.html", ["**XXLarge**"]),
    ],
)
async def test_font_formatting(tarsier, async_page, html_file, expected_text_content):
    font_formatting_html_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), f"mock_html/{html_file}")
    )
    await async_page.goto(f"file://{font_formatting_html_path}")
    page_text, tag_to_xpath = await tarsier.page_to_text(
        async_page, tagless=True, tag_text_elements=True
    )

    for expected_line in expected_text_content:
        assert (
            expected_line in page_text
        ), f"Expected text '{expected_line}' not found in the page content of {html_file}."
