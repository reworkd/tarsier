import time
import pytest
from bananalyzer.data.examples import get_training_examples
from playwright.async_api import async_playwright

example_data = [
    {
        "id": "h4q2uwr0z0sVFM0q5AV7n",
        "expected_page_to_image_time": 1.0,
        "expected_page_to_text_time": 3.0,
    },
    {
        "id": "7dhL1dij4AsT9qWCbWBHq",
        "expected_page_to_image_time": 6.0,
        "expected_page_to_text_time": 10.0,
    },
    {
        "id": "CsjbrXOwtX1rRqggZALRB",
        "expected_page_to_image_time": 1.0,
        "expected_page_to_text_time": 2.0,
    },
    {
        "id": "a0pJxHhxIHFKcoFjkORnG",
        "expected_page_to_image_time": 1.0,
        "expected_page_to_text_time": 1.5,
    },
    {
        "id": "4Je6qSd4YFoyLxVZLQRb7",
        "expected_page_to_image_time": 0.5,
        "expected_page_to_text_time": 1.5,
    },
    {
        "id": "u3fjwZRjKUEcvr8kkmy5v",
        "expected_page_to_image_time": 2.0,
        "expected_page_to_text_time": 5.0,
    },
    {
        "id": "1JWoJWs3uZMt8Wa5ql6pr",
        "expected_page_to_image_time": 3.5,
        "expected_page_to_text_time": 4.2,
    },
    {
        "id": "nxkcxrThdmaRX01YRXtho",
        "expected_page_to_image_time": 2.0,
        "expected_page_to_text_time": 5,
    },
    {
        "id": "BBofvHlOP5C5aSVJknz1C",
        "expected_page_to_image_time": 0.9,
        "expected_page_to_text_time": 3.5,
    },
    {
        "id": "7xlvZTTi21A1s7k3AoBOS",
        "expected_page_to_image_time": 2.0,
        "expected_page_to_text_time": 5.5,
    },
    {
        "id": "ct6PuXzujbOlM9zaARUpa",
        "expected_page_to_image_time": 3.0,
        "expected_page_to_text_time": 12.0,
    },
    {
        "id": "bwwko5J7aFk5K8qz61jBI",
        "expected_page_to_image_time": 1.0,
        "expected_page_to_text_time": 4,
    },
    {
        "id": "24SLE3KnDhtOYYgIM4ote",
        "expected_page_to_image_time": 1.0,
        "expected_page_to_text_time": 3.5,
    },
    {
        "id": "qtRibcsG6iq09TyGQoYhv",
        "expected_page_to_image_time": 3.0,
        "expected_page_to_text_time": 6.5,
    },
    {
        "id": "RVotqLcMUyKXULUTqYCvm",
        "expected_page_to_image_time": 2.0,
        "expected_page_to_text_time": 2.2,
    },
]

all_examples = get_training_examples()
examples = [
    {
        "example": example,
        "expected_page_to_image_time": data["expected_page_to_image_time"],
        "expected_page_to_text_time": data["expected_page_to_text_time"],
    }
    for data in example_data
    for example in all_examples
    if example.id == data["id"]
]


@pytest.mark.skip("need to update CI")
@pytest.mark.asyncio
@pytest.mark.parametrize("data", examples)
async def test_snapshot_execution_time(data, tarsier):
    example = data["example"]
    expected_image_time = data["expected_page_to_image_time"]
    expected_text_time = data["expected_page_to_text_time"]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1440, "height": 1024})
        await page.goto(example.get_static_url())
        await page.wait_for_timeout(3000)

        start_time = time.perf_counter()
        image, _ = await tarsier.page_to_image(page, tag_text_elements=True)
        image_duration = time.perf_counter() - start_time

        start_time = time.perf_counter()
        page_text, _ = await tarsier.page_to_text(page, tag_text_elements=True)
        text_duration = time.perf_counter() - start_time
        assert image_duration < expected_image_time, (
            f"Test failed for example ID: {example.id}\n"
            f"Expected 'page_to_image' to complete in under {expected_image_time:.2f} seconds, "
            f"but it took {image_duration:.2f} seconds."
        )
        assert text_duration < expected_text_time, (
            f"Test failed for example ID: {example.id}\n"
            f"Expected 'page_to_text' to complete in under {expected_text_time:.2f} seconds, "
            f"but it took {text_duration:.2f} seconds."
        )

        await browser.close()
