import os

import pytest
from playwright.async_api import async_playwright

example_data = [
    {
        "file_name": "test_artifact_page.mhtml",
        "artifact_selectors": [
            "[__tarsier_id]"
        ],  # TODO: add more selectors once colour tagging is merged
    },
]


@pytest.mark.parametrize("data", example_data)
@pytest.mark.asyncio
async def test_artifact_removal(data, tarsier):
    file_name = data["file_name"]
    artifact_selectors = data["artifact_selectors"]

    # Construct the path to the HTML file
    html_file_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "mock_html", file_name)
    )

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto(f"file://{html_file_path}")

        _, _ = await tarsier.page_to_text(page, tag_text_elements=True)

        # check if tarsier artifacts still exist
        for selector in artifact_selectors:
            elements = await page.query_selector_all(selector)
            assert (
                len(elements) == 0
            ), f"Tarsier artifact '{selector}' still exists in file: {file_name}"

        await browser.close()
