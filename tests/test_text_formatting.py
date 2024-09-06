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
async def test_font_formatting(
    tarsier, page_context_manager, html_file, expected_text_content
):
    async with page_context_manager(html_file) as page:
        page_text, tag_to_xpath = await tarsier.page_to_text(
            page, tagless=True, tag_text_elements=True
        )

    for expected_line in expected_text_content:
        assert (
            expected_line in page_text
        ), f"Expected text '{expected_line}' not found in the page content of {html_file}."
