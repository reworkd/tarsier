import pytest
from playwright.async_api import async_playwright
from bananalyzer.data.examples import get_training_examples

example_data = [
    {
        "id": "7xlvZTTi21A1s7k3AoBOS",
        "artifact_selectors": [
            "[__tarsier_id]"
        ],  # TODO: add more selectors once colour tagging is merged
    },
]

all_examples = get_training_examples()
examples = [
    {"example": example, "artifact_selectors": data["artifact_selectors"]}
    for data in example_data
    for example in all_examples
    if example.id == data["id"]
]


@pytest.mark.parametrize("data", examples)
@pytest.mark.asyncio
async def test_artifact_removal(data, tarsier):
    example = data["example"]
    artifact_selectors = data["artifact_selectors"]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1440, "height": 1024})

        await page.goto(example.get_static_url())
        await page.wait_for_timeout(3000)

        _, _ = await tarsier.page_to_text(page, tag_text_elements=True)

        # check if tarsier artifacts still exist
        for selector in artifact_selectors:
            elements = await page.query_selector_all(selector)
            assert (
                len(elements) == 0
            ), f"Tarsier artifact '{selector}' still exists for example ID: {example.id}"

        await browser.close()
