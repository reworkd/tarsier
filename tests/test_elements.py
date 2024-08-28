import os

import pytest

from tarsier import Tarsier, DummyOCRService


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "html_file, expected_tag_to_xpath, expected_page_text, expected_tag_string",
    [
        (
            "mock_html/text_only.html",
            {0: "//html/body/h1"},
            ["Hello, World!"],
            ["[ 0 ]"],
        ),
        (
            "mock_html/hyperlink_only.html",
            {0: '//html/body/p/a[@id="link1"]'},
            ["Example Link 1"],
            ["[ @ 0 ]"],
        ),
        (
            "mock_html/interactable_only.html",
            {
                0: '//html/body/button[@id="button"]',
                1: '//html/body/input[@id="checkbox"]',
            },
            ["Click Me"],
            ["[ $ 0 ]", "[ $ 1 ]"],
        ),
        (
            "mock_html/combination.html",
            {
                0: '//html/body/input[1][@id="text"]',
                1: '//html/body/input[2][@id="checkbox"]',
                2: "//html/body/p",
            },
            ["Enter text here", "Some random text"],
            ["[ # 0 ]", "[ $ 1 ]", "[ 2 ]"],
        ),
        (
            "mock_html/insertable_only.html",
            {0: '//html/body/input[@id="text"]'},
            ["Enter text here"],
            ["[ # 0 ]"],
        ),
        (
            "mock_html/br_elem.html",
            {
                0: "//html/body/div",
                1: "//html/body/div",
                2: "//html/body/div",
            },
            ["168 North Brent Street, Suite 401", "Ventura, CA 93003", "805-948-5093"],
            ["[ 0 ]", " [ 1 ]", "[ 2 ]"],
        ),
        (
            "mock_html/display_contents.html",
            {
                0: "//html/body/div",
            },
            ["Display contents"],
            ["[ 0 ]"],
        ),
        (
            "mock_html/icon_buttons.html",
            {
                0: "//html/body/button[1]",
                1: "//html/body/button[2]",
            },
            [],
            ["[ $ 0 ]", "[ $ 1 ]"],
        )
    ],
)
async def test_combined_elements_page(
    tarsier,
    async_page,
    html_file,
    expected_tag_to_xpath,
    expected_page_text,
    expected_tag_string,
):
    html_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), html_file))
    await async_page.goto(f"file://{html_file_path}")

    page_text, tag_to_xpath = await tarsier.page_to_text(
        async_page, tag_text_elements=True
    )

    assert tag_to_xpath == expected_tag_to_xpath, (
        f"tag_to_xpath does not match expected output for "
        f"{html_file}. Got: {tag_to_xpath}"
    )

    for expected_text in expected_page_text:
        assert expected_text in page_text, (
            f"Expected text '{expected_text}' not found in page text for {html_file}. "
            f"Got: {page_text}"
        )

    for expected_tag in expected_tag_string:
        assert expected_tag in page_text, (
            f"Expected tag '{expected_tag}' not found in page text for {html_file}. "
            f"Got: {page_text}"
        )


@pytest.mark.asyncio
async def test_text_nodes_are_query_selectable(async_page):
    text_node_html_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "mock_html/text_nodes.html")
    )
    await async_page.goto(f"file://{text_node_html_path}")
    tarsier = Tarsier(DummyOCRService())
    _, tag_to_xpath = await tarsier.page_to_text(async_page, tag_text_elements=True)

    # Query selector will specifically filter out TextNodes within XPath selectors
    # As a result, the tagged xpath for the text node should belong to the parent
    # https://github.com/microsoft/playwright/blob/main/packages/playwright-core/src/server/injected/xpathSelectorEngine.ts#L29-L30)
    assert len(tag_to_xpath) == 2
    assert await async_page.query_selector(tag_to_xpath[0])
    assert await async_page.query_selector(tag_to_xpath[1])
