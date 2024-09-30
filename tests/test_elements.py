import os

import pytest

from tarsier import Tarsier, DummyOCRService

IS_GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "html_file, expected_tag_metadata, expected_page_text",
    [
        (
            "text_only.html",
            [
                {
                    "xpath": "//html/body/h1",
                    "opening_tag_html": "<h1>",
                    "element_name": "h1",
                    "element_text": "Hello, World!",
                    "text_node_index": 1,
                    "id_symbol": "",
                    "id_string": "[ 0 ]",
                    "tarsier_id": 0,
                }
            ],
            ["Hello, World!"],
        ),
        (
            "hyperlink_only.html",
            [
                {
                    "xpath": '//html/body/p/a[@id="link1"]',
                    "opening_tag_html": '<a href="https://www.example.com" id="link1">',
                    "element_name": "a",
                    "element_text": "Example Link 1",
                    "text_node_index": None,
                    "id_symbol": "@",
                    "id_string": "[ @ 0 ]",
                    "tarsier_id": 0,
                }
            ],
            ["Example Link 1"],
        ),
        (
            "interactable_only.html",
            [
                {
                    "xpath": '//html/body/button[@id="button"]',
                    "opening_tag_html": '<button id="button" style="font-size: 20px">',
                    "element_name": "button",
                    "element_text": "Click Me",
                    "text_node_index": None,
                    "id_symbol": "$",
                    "id_string": "[ $ 0 ]",
                    "tarsier_id": 0,
                },
                {
                    "xpath": '//html/body/input[@id="checkbox"]',
                    "opening_tag_html": '<input type="checkbox" id="checkbox" name="checkbox">',
                    "element_name": "input",
                    "element_text": None,
                    "text_node_index": None,
                    "id_symbol": "$",
                    "id_string": "[ $ 1 ]",
                    "tarsier_id": 1,
                },
            ],
            ["Click Me"],
        ),
        (
            "combination.html",
            [
                {
                    "xpath": '//html/body/input[1][@id="text"]',
                    "opening_tag_html": '<input type="text" id="text" name="text" placeholder="Enter text here" style="font-size: 20px">',
                    "element_name": "input",
                    "element_text": None,
                    "text_node_index": None,
                    "id_symbol": "#",
                    "id_string": "[ # 0 ]",
                    "tarsier_id": 0,
                },
                {
                    "xpath": '//html/body/input[2][@id="checkbox"]',
                    "opening_tag_html": '<input type="checkbox" id="checkbox" name="checkbox">',
                    "element_name": "input",
                    "element_text": None,
                    "text_node_index": None,
                    "id_symbol": "$",
                    "id_string": "[ $ 1 ]",
                    "tarsier_id": 1,
                },
                {
                    "xpath": "//html/body/p",
                    "opening_tag_html": '<p style="font-size: 20px">',
                    "element_name": "p",
                    "element_text": "Some random text",
                    "text_node_index": 1,
                    "id_symbol": "",
                    "id_string": "[ 2 ]",
                    "tarsier_id": 2,
                },
            ],
            ["Enter text here", "Some random text"],
        ),
        (
            "insertable_only.html",
            [
                {
                    "xpath": '//html/body/input[@id="text"]',
                    "opening_tag_html": '<input type="text" id="text" name="text" placeholder="Enter text here" style="font-size: 20px">',
                    "element_name": "input",
                    "element_text": None,
                    "text_node_index": None,
                    "id_symbol": "#",
                    "id_string": "[ # 0 ]",
                    "tarsier_id": 0,
                }
            ],
            ["Enter text here"],
        ),
        (
            "br_elem.html",
            [
                {
                    "xpath": "//html/body/div",
                    "opening_tag_html": '<div style="display: inline-block">',
                    "element_name": "div",
                    "element_text": "168 North Brent Street, Suite 401",
                    "text_node_index": 1,
                    "id_symbol": "",
                    "id_string": "[ 0 ]",
                    "tarsier_id": 0,
                },
                {
                    "xpath": "//html/body/div",
                    "opening_tag_html": '<div style="display: inline-block">',
                    "element_name": "div",
                    "element_text": "Ventura, CA 93003",
                    "text_node_index": 2,
                    "id_symbol": "",
                    "id_string": "[ 1 ]",
                    "tarsier_id": 1,
                },
                {
                    "xpath": "//html/body/div",
                    "opening_tag_html": '<div style="display: inline-block">',
                    "element_name": "div",
                    "element_text": "805-948-5093",
                    "text_node_index": 3,
                    "id_symbol": "",
                    "id_string": "[ 2 ]",
                    "tarsier_id": 2,
                },
            ],
            ["168 North Brent Street, Suite 401", "Ventura, CA 93003", "805-948-5093"],
        ),
        (
            "display_contents.html",
            [
                {
                    "tarsier_id": 0,
                    "element_name": "div",
                    "opening_tag_html": '<div style="display: contents; font-size: 2.5em">',
                    "xpath": "//html/body/div",
                    "element_text": "Display contents elements technically have 0 width and height",
                    "text_node_index": 1,
                    "id_symbol": "",
                    "id_string": "[ 0 ]",
                },
            ],
            ["Display contents elements technically have 0 width and height"],
        ),
        (
            "icon_buttons.html",
            [
                {
                    "tarsier_id": 0,
                    "element_name": "button",
                    "opening_tag_html": "<button>",
                    "xpath": "//html/body/button[1]",
                    "element_text": None,
                    "text_node_index": None,
                    "id_symbol": "$",
                    "id_string": "[ $ 0 ]",
                },
                {
                    "tarsier_id": 1,
                    "element_name": "button",
                    "opening_tag_html": "<button>",
                    "xpath": "//html/body/button[2]",
                    "element_text": None,
                    "text_node_index": None,
                    "id_symbol": "$",
                    "id_string": "[ $ 1 ]",
                },
            ],
            [],
        ),
        (
            "image.html",
            [
                {
                    "tarsier_id": 0,
                    "element_name": "img",
                    "opening_tag_html": '<img src="https://placehold.co/200x200/black/white/?text=Hello+World" alt="Image with Text">',
                    "xpath": "//html/body/img",
                    "element_text": None,
                    "text_node_index": None,
                    "id_symbol": "%",
                    "id_string": "[ % 0 ]",
                },
            ],
            ["Hello World"],
        ),
        pytest.param(
            "japanese.html",
            [
                {
                    "tarsier_id": 0,
                    "element_name": "p",
                    "opening_tag_html": '<p id="japanese">',
                    "xpath": '//html/body/p[@id="japanese"]',
                    "element_text": "こんにちは世界",
                    "text_node_index": 1,
                    "id_symbol": "",
                    "id_string": "[ 0 ]",
                },
            ],
            ["こんにちは世界"],
            marks=pytest.mark.skipif(
                IS_GITHUB_ACTIONS, reason="Skipping language test in CI"
            ),
        ),
        pytest.param(
            "russian.html",
            [
                {
                    "tarsier_id": 0,
                    "element_name": "p",
                    "opening_tag_html": '<p id="russian" style="padding-left: 50px">',
                    "xpath": '//html/body/p[@id="russian"]',
                    "element_text": "Привет, мир",
                    "text_node_index": 1,
                    # 'id_symbol': '',
                    # 'id_string': '[ 0 ]',
                },
            ],
            ["Привет, мир"],
            marks=pytest.mark.skipif(
                IS_GITHUB_ACTIONS, reason="Skipping language test in CI"
            ),
        ),
        pytest.param(
            "chinese.html",
            [
                {
                    "tarsier_id": 0,
                    "element_name": "p",
                    "opening_tag_html": '<p id="chinese">',
                    "xpath": '//html/body/p[@id="chinese"]',
                    "element_text": "你好, 世界",
                    "text_node_index": 1,
                    "id_symbol": "",
                    "id_string": "[ 0 ]",
                },
            ],
            ["你好, 世界"],
            marks=pytest.mark.skipif(
                IS_GITHUB_ACTIONS, reason="Skipping language test in CI"
            ),
        ),
        pytest.param(
            "arabic.html",
            [
                {
                    "tarsier_id": 0,
                    "element_name": "p",
                    "opening_tag_html": '<p id="arabic">',
                    "xpath": '//html/body/p[@id="arabic"]',
                    "element_text": "مرحبا بالعالم",
                    "text_node_index": 1,
                    # 'id_symbol': '',
                    # 'id_string': '[ 0 ]',
                },
            ],
            ["مرحبا بالعالم"],
            marks=pytest.mark.skipif(
                IS_GITHUB_ACTIONS, reason="Skipping language test in CI"
            ),
        ),
        pytest.param(
            "hindi.html",
            [
                {
                    "tarsier_id": 0,
                    "element_name": "p",
                    "opening_tag_html": '<p id="hindi">',
                    "xpath": '//html/body/p[@id="hindi"]',
                    "element_text": "नमस्ते दुनिया",
                    "text_node_index": 1,
                    "id_symbol": "",
                    "id_string": "[ 0 ]",
                },
            ],
            ["नमस्ते दुनिया"],
            marks=pytest.mark.skipif(
                IS_GITHUB_ACTIONS, reason="Skipping language test in CI"
            ),
        ),
        (
            "dropdown.html",
            [
                {
                    "tarsier_id": 0,
                    "element_name": "label",
                    "opening_tag_html": "<label>",
                    "xpath": "//html/body/label",
                    "element_text": "Option 1\n        Option 2\n        Option 3\n        Option 4",
                    "text_node_index": None,
                    "id_symbol": "$",
                    "id_string": "[ $ 0 ]",
                },
            ],
            ["Option 1"],
        ),
        (
            "iframe.html",
            [
                {
                    "tarsier_id": 0,
                    "element_name": "p",
                    "opening_tag_html": '<p iframe_index="0">',
                    "xpath": "iframe[0]//html/body/p",
                    "element_text": "This is some text content inside the iframe",
                    "text_node_index": 1,
                    "id_symbol": "",
                    "id_string": "[ 0 ]",
                },
            ],
            ["This is some text content inside the iframe"],
        ),
        (
            "image_inside_button.html",
            [
                {
                    "tarsier_id": 0,
                    "element_name": "button",
                    "opening_tag_html": '<button id="image-button">',
                    "xpath": '//html/body/button[@id="image-button"]',
                    "element_text": None,
                    "text_node_index": None,
                    "id_symbol": "$",
                    "id_string": "[ $ 0 ]",
                },
            ],
            [],
        ),
        (
            "image_and_text.html",
            [
                {
                    "tarsier_id": 0,
                    "element_name": "img",
                    "opening_tag_html": '<img src="https://placehold.co/200x200?text=`" alt="An image" style="float: left; margin-right: 10px">',
                    "xpath": "//html/body/div/img",
                    "element_text": None,
                    "text_node_index": None,
                    "id_symbol": "%",
                    "id_string": "[ % 0 ]",
                },
                {
                    "tarsier_id": 1,
                    "element_name": "p",
                    "opening_tag_html": "<p>",
                    "xpath": "//html/body/div/p",
                    "element_text": "Some text next to an image",
                    "text_node_index": 1,
                    "id_symbol": "",
                    "id_string": "[ 1 ]",
                },
            ],
            ["Some text next to an image"],
        ),
        (
            "different_image_sizes.html",
            [
                {
                    "tarsier_id": 0,
                    "element_name": "img",
                    "opening_tag_html": '<img id="small" src="https://placehold.co/60x60?text=+" alt="Small Image">',
                    "xpath": '//html/body/img[1][@id="small"]',
                    "element_text": None,
                    "text_node_index": None,
                    "id_symbol": "%",
                    "id_string": "[ % 0 ]",
                },
                {
                    "tarsier_id": 1,
                    "element_name": "img",
                    "opening_tag_html": '<img id="medium" src="https://placehold.co/250x250?text=+" alt="Medium Image">',
                    "xpath": '//html/body/img[2][@id="medium"]',
                    "element_text": None,
                    "text_node_index": None,
                    "id_symbol": "%",
                    "id_string": "[ % 1 ]",
                },
                {
                    "tarsier_id": 2,
                    "element_name": "img",
                    "opening_tag_html": '<img id="large" src="https://placehold.co/600x600?text=+" alt="Large Image">',
                    "xpath": '//html/body/img[3][@id="large"]',
                    "element_text": None,
                    "text_node_index": None,
                    "id_symbol": "%",
                    "id_string": "[ % 2 ]",
                },
            ],
            [],
        ),
        (
            "hidden_image.html",
            [
                {
                    "tarsier_id": 0,
                    "element_name": "img",
                    "opening_tag_html": '<img src="https://placehold.co/100x100?text=+" alt="Visible Image" class="visible" id="visible-image">',
                    "xpath": '//html/body/img[1][@id="visible-image"]',
                    "element_text": None,
                    "text_node_index": None,
                    "id_symbol": "%",
                    "id_string": "[ % 0 ]",
                },
            ],
            [],
        ),
        (
            "image_inside_link.html",
            [
                {
                    "tarsier_id": 0,
                    "element_name": "a",
                    "opening_tag_html": '<a href="http://example.com" id="link1">',
                    "xpath": '//html/body/a[@id="link1"]',
                    "element_text": None,
                    "text_node_index": None,
                    "id_symbol": "@",
                    "id_string": "[ @ 0 ]",
                },
            ],
            [],
        ),
        (
            "invalid_text_nodes.html",
            [
                {
                    "xpath": "//html/body/div",
                    "opening_tag_html": '<div style="font-size: xx-large">',
                    "element_name": "div",
                    "element_text": "Index 2",
                    "text_node_index": 2,
                    "id_symbol": "",
                    "id_string": "[ 0 ]",
                    "tarsier_id": 0,
                },
                {
                    "xpath": "//html/body/div",
                    "opening_tag_html": '<div style="font-size: xx-large">',
                    "element_name": "div",
                    "element_text": "Index 3",
                    "text_node_index": 3,
                    "id_symbol": "",
                    "id_string": "[ 1 ]",
                    "tarsier_id": 1,
                },
            ],
            ["Index 2 Index 3"],
        ),
        (
            "full_xpath.html",
            [
                {
                    "tarsier_id": 0,
                    "element_name": "p",
                    "opening_tag_html": '<p class="text">',
                    "xpath": '//div[@id="column"]/div[@class="row"]/div[@class="level1"]/div[@class="level2"]/div[@class="level3"]/p[@class="text"]',
                    "element_text": "Sample text 1",
                    "text_node_index": 1,
                    "id_symbol": "",
                    "id_string": "[ 0 ]",
                },
            ],
            ["Sample text 1"],
        ),
    ],
)
async def test_combined_elements_page_detailed(
    tarsier,
    page_context,
    html_file,
    expected_tag_metadata,
    expected_page_text,
):
    async with page_context(html_file) as page:
        page_text, tag_metadata_list = await tarsier.page_to_text(
            page, tag_text_elements=True
        )

        for expected_values in expected_tag_metadata:
            tarsier_id = expected_values["tarsier_id"]
            matching_tag = next(
                (tag for tag in tag_metadata_list if tag["tarsier_id"] == tarsier_id),
                None,
            )
            assert (
                matching_tag
            ), f"Tag with tarsier_id '{tarsier_id}' not found in tag_metadata_list"

            for key, expected_value in expected_values.items():
                actual_value = matching_tag.get(key, None)
                assert actual_value == expected_value, (
                    f"Expected {key} '{expected_value}' does not match actual "
                    f"'{actual_value}' for tarsierID '{tarsier_id}'"
                )

        normalized_expected_text = "".join(expected_page_text).replace(" ", "")
        page_text_combined = "".join(page_text).replace(" ", "")

        assert all(
            char in page_text_combined for char in normalized_expected_text
        ), f"Expected text '{expected_page_text}' not found in page text. Got: {page_text}"

        expected_tag_strings = [
            tag["id_string"] for tag in expected_tag_metadata if "id_string" in tag
        ]
        for expected_tag in expected_tag_strings:
            assert (
                expected_tag in page_text
            ), f"Expected tag '{expected_tag}' not found in page text. Got: {page_text}"


@pytest.mark.asyncio
async def test_text_nodes_are_query_selectable(page_context):
    async with page_context("text_nodes.html") as page:
        tarsier = Tarsier(DummyOCRService())
        _, tag_to_xpath = await tarsier.page_to_text(page, tag_text_elements=True)

        # Query selector will specifically filter out TextNodes within XPath selectors
        # As a result, the tagged xpath for the text node should belong to the parent
        # https://github.com/microsoft/playwright/blob/main/packages/playwright-core/src/server/injected/xpathSelectorEngine.ts#L29-L30)
        assert len(tag_to_xpath) == 2
        for tag_metadata in tag_to_xpath:
            xpath = tag_metadata["xpath"]
            assert await page.query_selector(xpath), f"XPath '{xpath}' not selectable"


@pytest.mark.asyncio
async def test_dropdown_text_not_shown(tarsier, page_context):
    async with page_context("dropdown.html") as page:
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
