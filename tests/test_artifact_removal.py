import os

import pytest
from playwright.async_api import async_playwright

example_data = [
    {
        "file_name": "test_artifact_page.mhtml",
        "artifact_selectors": [
            "#__tarsier_id",
        ],  # TODO: add more selectors once colour tagging is merged
    },
]

tarsier_functions = [
    (
        "page_to_text",
        {"tag_text_elements": True, "keep_tags_showing": True},
        ["remove_tags"],
    ),
    # ("page_to_text_colour_tag", {}),  # TODO: Uncomment this line once page_to_text_colour_tag is merged
]


@pytest.mark.parametrize("data", example_data)
@pytest.mark.parametrize(
    "function_name, function_kwargs, cleanup_functions", tarsier_functions
)
@pytest.mark.asyncio
async def test_artifact_removal(
    data, function_name, function_kwargs, cleanup_functions, tarsier
):
    file_name = data["file_name"]
    artifact_selectors = data["artifact_selectors"]

    # Construct the path to the HTML file
    html_file_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "mock_html", file_name)
    )

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        await page.goto(f"file://{html_file_path}")

        tarsier_func = getattr(tarsier, function_name)
        _, _ = await tarsier_func(page, **function_kwargs)

        # check if tarsier artifacts still exist
        for selector in artifact_selectors:
            elements = await page.query_selector_all(selector)
            assert len(elements) > 0, (
                f"Tarsier artifact '{selector}' not found in file: {file_name} "
                f"after calling {function_name} with keep_tags_showing=True"
            )

        # run cleanup function(s)
        for cleanup_function in cleanup_functions:
            cleanup_func = getattr(tarsier, cleanup_function)
            await cleanup_func(page)

        # check that attributes no longer exist
        for selector in artifact_selectors:
            elements = await page.query_selector_all(selector)
            assert len(elements) == 0, (
                f"Tarsier artifact '{selector}' still exists in file: {file_name} "
                f"after calling cleanup functions: {', '.join(cleanup_functions)}"
            )

        await browser.close()
