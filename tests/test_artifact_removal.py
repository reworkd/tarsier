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


def create_tarsier_functions(tarsier):
    return [
        (
            lambda page: tarsier.page_to_text(
                page, tag_text_elements=True, keep_tags_showing=True
            ),
            [lambda page: tarsier.remove_tags(page)],
        ),
        # TODO: Uncomment and adjust once colour tagging is merged
        # (
        #     lambda page: tarsier.page_to_text_colour_tag(page, keep_tags_showing=True),
        #     [
        #         lambda page: tarsier.remove_colour_tags(page),
        #         lambda page: tarsier.remove_tags(page)
        #     ]
        # ),
    ]


@pytest.mark.parametrize("data", example_data)
@pytest.mark.asyncio
async def test_artifact_removal(data, tarsier):
    file_name = data["file_name"]
    artifact_selectors = data["artifact_selectors"]

    html_file_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "mock_html", file_name)
    )

    tarsier_functions = create_tarsier_functions(tarsier)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto(f"file://{html_file_path}")

        for tarsier_func, cleanup_funcs in tarsier_functions:
            await tarsier_func(page)

            # check if tarsier artifacts exist
            for selector in artifact_selectors:
                elements = await page.query_selector_all(selector)
                assert len(elements) > 0, (
                    f"Tarsier artifact '{selector}' not found in file: {file_name} "
                    f"after applying tarsier function"
                )

            # run cleanup functions
            for cleanup_func in cleanup_funcs:
                await cleanup_func(page)

            # check that attributes no longer exist
            for selector in artifact_selectors:
                elements = await page.query_selector_all(selector)
                assert len(elements) == 0, (
                    f"Tarsier artifact '{selector}' still exists in file: {file_name} "
                    f"after applying cleanup functions"
                )

        await browser.close()
