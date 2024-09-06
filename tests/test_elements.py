import os

import pytest

from tarsier import Tarsier, DummyOCRService

IS_GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "html_file, expected_tag_to_xpath, expected_page_text, expected_tag_string",
    [
        (
            "text_only.html",
            {0: "//html/body/h1"},
            ["Hello, World!"],
            ["[ 0 ]"],
        ),
        (
            "hyperlink_only.html",
            {0: '//html/body/p/a[@id="link1"]'},
            ["Example Link 1"],
            ["[ @ 0 ]"],
        ),
        (
            "interactable_only.html",
            {
                0: '//html/body/button[@id="button"]',
                1: '//html/body/input[@id="checkbox"]',
            },
            ["Click Me"],
            ["[ $ 0 ]", "[ $ 1 ]"],
        ),
        (
            "combination.html",
            {
                0: '//html/body/input[1][@id="text"]',
                1: '//html/body/input[2][@id="checkbox"]',
                2: "//html/body/p",
            },
            ["Enter text here", "Some random text"],
            ["[ # 0 ]", "[ $ 1 ]", "[ 2 ]"],
        ),
        (
            "insertable_only.html",
            {0: '//html/body/input[@id="text"]'},
            ["Enter text here"],
            ["[ # 0 ]"],
        ),
        (
            "br_elem.html",
            {
                0: "//html/body/div",
                1: "//html/body/div",
                2: "//html/body/div",
            },
            ["168 North Brent Street, Suite 401", "Ventura, CA 93003", "805-948-5093"],
            ["[ 0 ]", "[ 1 ]", "[ 2 ]"],
        ),
        (
            "display_contents.html",
            {
                0: "//html/body/div",
            },
            ["Display contents"],
            ["[ 0 ]"],
        ),
        (
            "icon_buttons.html",
            {
                0: "//html/body/button[1]",
                1: "//html/body/button[2]",
            },
            [],
            ["[ $ 0 ]", "[ $ 1 ]"],
        ),
        (
            "image.html",
            {},
            ["Hello World"],
            [],
        ),
        pytest.param(
            "japanese.html",
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
            "russian.html",
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
            "chinese.html",
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
            "arabic.html",
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
            "hindi.html",
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
            "dropdown.html",
            {
                0: "//html/body/label",
            },
            ["Option 1"],
            ["[ $ 0 ]"],
        ),
        (
            "iframe.html",
            {
                0: "iframe[0]//html/body/p",
            },
            ["This is some text content inside the iframe"],
            ["[ 0 ]"],
        ),
    ],
)
async def test_combined_elements_page(
    tarsier,
    page_context_manager,
    html_file,
    expected_tag_to_xpath,
    expected_page_text,
    expected_tag_string,
):
    async with page_context_manager(html_file) as page:
        page_text, tag_to_xpath = await tarsier.page_to_text(
            page, tag_text_elements=True
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

            assert all(
                char in page_text_combined for char in normalized_expected_text
            ), (
                f"Expected text '{expected_text}' not found in page text for {html_file}. "
                f"Got: {page_text}"
            )

        for expected_tag in expected_tag_string:
            assert expected_tag in page_text, (
                f"Expected tag '{expected_tag}' not found in page text for {html_file}. "
                f"Got: {page_text}"
            )


@pytest.mark.asyncio
async def test_text_nodes_are_query_selectable(page_context_manager):
    async with page_context_manager("text_nodes.html") as page:
        tarsier = Tarsier(DummyOCRService())
        _, tag_to_xpath = await tarsier.page_to_text(page, tag_text_elements=True)

        # Query selector will specifically filter out TextNodes within XPath selectors
        # As a result, the tagged xpath for the text node should belong to the parent
        # https://github.com/microsoft/playwright/blob/main/packages/playwright-core/src/server/injected/xpathSelectorEngine.ts#L29-L30)
        assert len(tag_to_xpath) == 2
        assert await page.query_selector(tag_to_xpath[0])
        assert await page.query_selector(tag_to_xpath[1])


@pytest.mark.asyncio
async def test_dropdown_text_not_shown(tarsier, page_context_manager):
    async with page_context_manager("dropdown.html") as page:
        page_text, tag_to_xpath = await tarsier.page_to_text(
            page, tag_text_elements=True
        )

        assert "[ $ 1 ]" not in page_text
        assert "[ $ 2 ]" not in page_text
        assert "[ $ 3 ]" not in page_text
        assert "[ $ 4 ]" not in page_text
        assert "Option 2" not in page_text
        assert "Option 3" not in page_text
        assert "Option 4" not in page_text
