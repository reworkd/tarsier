import os

import pytest

from tarsier import Tarsier, DummyOCRService

IS_GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"


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
        ),
        (
            "mock_html/image.html",
            {},
            ["Hello World"],
            [],
        ),
        pytest.param(
            "mock_html/japanese.html",
            {
                0: '//html/body/p[@id="japanese"]',
            },
            ["こんにちは世界"],
            ["[ 0 ]"],
            marks=pytest.mark.skipif(
                IS_GITHUB_ACTIONS, reason="Skipping language test in CI"
            ),
        ),
        pytest.param(
            "mock_html/russian.html",
            {
                0: '//html/body/p[@id="russian"]',
            },
            ["Привет, мир"],
            [],  # add tag back in here when testing colour tagging
            marks=pytest.mark.skipif(
                IS_GITHUB_ACTIONS, reason="Skipping language test in CI"
            ),
        ),
        pytest.param(
            "mock_html/chinese.html",
            {
                0: '//html/body/p[@id="chinese"]',
            },
            ["你好, 世界"],
            ["[ 0 ]"],
            marks=pytest.mark.skipif(
                IS_GITHUB_ACTIONS, reason="Skipping language test in CI"
            ),
        ),
        pytest.param(
            "mock_html/arabic.html",
            {
                0: '//html/body/p[@id="arabic"]',
            },
            ["مرحبا بالعالم"],
            [],  # add tag back in here when testing colour tagging
            marks=pytest.mark.skipif(
                IS_GITHUB_ACTIONS, reason="Skipping language test in CI"
            ),
        ),
        pytest.param(
            "mock_html/hindi.html",
            {
                0: '//html/body/p[@id="hindi"]',
            },
            ["नमस्ते दुनिया"],
            ["[ 0 ]"],
            marks=pytest.mark.skipif(
                IS_GITHUB_ACTIONS, reason="Skipping language test in CI"
            ),
        ),
        (
            "mock_html/dropdown.html",
            {
                0: "//html/body/label",
            },
            ["Option 1"],
            ["[ $ 0 ]"],
        ),
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

    # TODO: revert to testing against entire string when colour tagging is merged
    for expected_text in expected_page_text:
        normalized_expected_text = "".join(
            expected_text.split()
        )  # Remove whitespace from expected text
        page_text_combined = "".join(page_text).replace(" ", "")

        assert all(char in page_text_combined for char in normalized_expected_text), (
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


@pytest.mark.asyncio
async def test_dropdown_text_not_shown(tarsier, async_page):
    dropdown_html_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "mock_html/dropdown.html")
    )
    await async_page.goto(f"file://{dropdown_html_path}")
    page_text, tag_to_xpath = await tarsier.page_to_text(
        async_page, tag_text_elements=True
    )

    assert "[ $ 1 ]" not in page_text
    assert "[ $ 2 ]" not in page_text
    assert "[ $ 3 ]" not in page_text
    assert "[ $ 4 ]" not in page_text
    assert "Option 2" not in page_text
    assert "Option 3" not in page_text
    assert "Option 4" not in page_text
