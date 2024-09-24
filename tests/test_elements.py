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
                    "elementHTML": "<h1>Hello, World!</h1>",
                    "elementName": "h1",
                    "elementText": "Hello, World!",
                    "textNodeIndex": 1,
                    "idSymbol": "",
                    "idString": "[ 0 ]",
                    "tarsierID": 0,
                }
            ],
            ["Hello, World!"],
        ),
        (
            "hyperlink_only.html",
            [
                {
                    "xpath": '//html/body/p/a[@id="link1"]',
                    "elementHTML": '<a href="https://www.example.com" id="link1">Example Link 1</a>',
                    "elementName": "a",
                    "elementText": "Example Link 1",
                    "textNodeIndex": None,
                    "idSymbol": "@",
                    "idString": "[ @ 0 ]",
                    "tarsierID": 0,
                }
            ],
            ["Example Link 1"],
        ),
        (
            "interactable_only.html",
            [
                {
                    "xpath": '//html/body/button[@id="button"]',
                    "elementHTML": '<button id="button" style="font-size: 20px">Click Me</button>',
                    "elementName": "button",
                    "elementText": "Click Me",
                    "textNodeIndex": None,
                    "idSymbol": "$",
                    "idString": "[ $ 0 ]",
                    "tarsierID": 0,
                },
                {
                    "xpath": '//html/body/input[@id="checkbox"]',
                    "elementHTML": '<input type="checkbox" id="checkbox" name="checkbox">',
                    "elementName": "input",
                    "elementText": None,
                    "textNodeIndex": None,
                    "idSymbol": "$",
                    "idString": "[ $ 1 ]",
                    "tarsierID": 1,
                },
            ],
            ["Click Me"],
        ),
        (
            "combination.html",
            [
                {
                    "xpath": '//html/body/input[1][@id="text"]',
                    "elementHTML": '<input type="text" id="text" name="text" placeholder="Enter text here" style="font-size: 20px">',
                    "elementName": "input",
                    "elementText": None,
                    "textNodeIndex": None,
                    "idSymbol": "#",
                    "idString": "[ # 0 ]",
                    "tarsierID": 0,
                },
                {
                    "xpath": '//html/body/input[2][@id="checkbox"]',
                    "elementHTML": '<input type="checkbox" id="checkbox" name="checkbox">',
                    "elementName": "input",
                    "elementText": None,
                    "textNodeIndex": None,
                    "idSymbol": "$",
                    "idString": "[ $ 1 ]",
                    "tarsierID": 1,
                },
                {
                    "xpath": "//html/body/p",
                    "elementHTML": '<p style="font-size: 20px">Some random text</p>',
                    "elementName": "p",
                    "elementText": "Some random text",
                    "textNodeIndex": 1,
                    "idSymbol": "",
                    "idString": "[ 2 ]",
                    "tarsierID": 2,
                },
            ],
            ["Enter text here", "Some random text"],
        ),
        (
            "insertable_only.html",
            [
                {
                    "xpath": '//html/body/input[@id="text"]',
                    "elementHTML": '<input type="text" id="text" name="text" placeholder="Enter text here" style="font-size: 20px">',
                    "elementName": "input",
                    "elementText": None,
                    "textNodeIndex": None,
                    "idSymbol": "#",
                    "idString": "[ # 0 ]",
                    "tarsierID": 0,
                }
            ],
            ["Enter text here"],
        ),
        (
            "br_elem.html",
            [
                {
                    "xpath": "//html/body/div",
                    "elementHTML": '<div style="display: inline-block">\n      168 North Brent Street, Suite 401\n      <br>\n      Ventura, CA 93003\n      <br>\n      805-948-5093\n    </div>',
                    "elementName": "div",
                    "elementText": "168 North Brent Street, Suite 401",
                    "textNodeIndex": 1,
                    "idSymbol": "",
                    "idString": "[ 0 ]",
                    "tarsierID": 0,
                },
                {
                    "xpath": "//html/body/div",
                    "elementHTML": '<div style="display: inline-block">\n      168 North Brent Street, Suite 401\n      <br>\n      Ventura, CA 93003\n      <br>\n      805-948-5093\n    </div>',
                    "elementName": "div",
                    "elementText": "Ventura, CA 93003",
                    "textNodeIndex": 2,
                    "idSymbol": "",
                    "idString": "[ 1 ]",
                    "tarsierID": 1,
                },
                {
                    "xpath": "//html/body/div",
                    "elementHTML": '<div style="display: inline-block">\n      168 North Brent Street, Suite 401\n      <br>\n      Ventura, CA 93003\n      <br>\n      805-948-5093\n    </div>',
                    "elementName": "div",
                    "elementText": "805-948-5093",
                    "textNodeIndex": 3,
                    "idSymbol": "",
                    "idString": "[ 2 ]",
                    "tarsierID": 2,
                },
            ],
            ["168 North Brent Street, Suite 401", "Ventura, CA 93003", "805-948-5093"],
        ),
        (
            "display_contents.html",
            [
                {
                    "tarsierID": 0,
                    "elementName": "div",
                    "elementHTML": '<div style="display: contents; font-size: 2.5em">\n      Display contents elements technically have 0 width and height\n    </div>',
                    "xpath": "//html/body/div",
                    "elementText": "Display contents elements technically have 0 width and height",
                    "textNodeIndex": 1,
                    "idSymbol": "",
                    "idString": "[ 0 ]",
                },
            ],
            ["Display contents elements technically have 0 width and height"],
        ),
        (
            "icon_buttons.html",
            [
                {
                    "tarsierID": 0,
                    "elementName": "button",
                    "elementHTML": '<button>\n      <svg width="100" height="100">\n        <rect x="50" y="20" rx="20" ry="20" width="150" height="150" style="fill: red; stroke: black; stroke-width: 5; opacity: 0.5"></rect>\n      </svg>\n    </button>',
                    "xpath": "//html/body/button[1]",
                    "elementText": None,
                    "textNodeIndex": None,
                    "idSymbol": "$",
                    "idString": "[ $ 0 ]",
                },
                {
                    "tarsierID": 1,
                    "elementName": "button",
                    "elementHTML": '<button>\n      <img>\n        <svg width="100" height="100">\n          <circle cx="50" cy="50" r="40" stroke="green" stroke-width="4" fill="yellow"></circle>\n        </svg>\n      \n    </button>',
                    "xpath": "//html/body/button[2]",
                    "elementText": None,
                    "textNodeIndex": None,
                    "idSymbol": "$",
                    "idString": "[ $ 1 ]",
                },
            ],
            [],
        ),
        (
            "image.html",
            [
                {
                    "tarsierID": 0,
                    "elementName": "img",
                    "elementHTML": '<img src="https://placehold.co/200x200/black/white/?text=Hello+World" alt="Image with Text">',
                    "xpath": "//html/body/img",
                    "elementText": None,
                    "textNodeIndex": None,
                    "idSymbol": "%",
                    "idString": "[ % 0 ]",
                },
            ],
            ["Hello World"],
        ),
        pytest.param(
            "japanese.html",
            [
                {
                    "tarsierID": 0,
                    "elementName": "p",
                    "elementHTML": '<p id="japanese">こんにちは世界</p>',
                    "xpath": '//html/body/p[@id="japanese"]',
                    "elementText": "こんにちは世界",
                    "textNodeIndex": 1,
                    "idSymbol": "",
                    "idString": "[ 0 ]",
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
                    "tarsierID": 0,
                    "elementName": "p",
                    "elementHTML": '<p id="russian" style="padding-left: 50px">Привет, мир</p>',
                    "xpath": '//html/body/p[@id="russian"]',
                    "elementText": "Привет, мир",
                    "textNodeIndex": 1,
                    # 'idSymbol': '',
                    # 'idString': '[ 0 ]',
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
                    "tarsierID": 0,
                    "elementName": "p",
                    "elementHTML": '<p id="chinese">你好, 世界</p>',
                    "xpath": '//html/body/p[@id="chinese"]',
                    "elementText": "你好, 世界",
                    "textNodeIndex": 1,
                    "idSymbol": "",
                    "idString": "[ 0 ]",
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
                    "tarsierID": 0,
                    "elementName": "p",
                    "elementHTML": '<p id="arabic">مرحبا بالعالم</p>',
                    "xpath": '//html/body/p[@id="arabic"]',
                    "elementText": "مرحبا بالعالم",
                    "textNodeIndex": 1,
                    # 'idSymbol': '',
                    # 'idString': '[ 0 ]',
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
                    "tarsierID": 0,
                    "elementName": "p",
                    "elementHTML": '<p id="hindi">नमस्ते दुनिया</p>',
                    "xpath": '//html/body/p[@id="hindi"]',
                    "elementText": "नमस्ते दुनिया",
                    "textNodeIndex": 1,
                    "idSymbol": "",
                    "idString": "[ 0 ]",
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
                    "tarsierID": 0,
                    "elementName": "label",
                    "elementHTML": '<label>\n      <select style="font-size: xx-large">\n        <option value="option1">Option 1</option>\n        <option value="option2">Option 2</option>\n        <option value="option3">Option 3</option>\n        <option value="option4">Option 4</option>\n      </select>\n    </label>',
                    "xpath": "//html/body/label",
                    "elementText": "Option 1\n        Option 2\n        Option 3\n        Option 4",
                    "textNodeIndex": None,
                    "idSymbol": "$",
                    "idString": "[ $ 0 ]",
                },
            ],
            ["Option 1"],
        ),
        (
            "iframe.html",
            [
                {
                    "tarsierID": 0,
                    "elementName": "p",
                    "elementHTML": '<p iframe_index="0">This is some text content inside the iframe</p>',
                    "xpath": "iframe[0]//html/body/p",
                    "elementText": "This is some text content inside the iframe",
                    "textNodeIndex": 1,
                    "idSymbol": "",
                    "idString": "[ 0 ]",
                },
            ],
            ["This is some text content inside the iframe"],
        ),
        (
            "image_inside_button.html",
            [
                {
                    "tarsierID": 0,
                    "elementName": "button",
                    "elementHTML": '<button id="image-button">\n      <img src="https://placehold.co/200x200?text=`" alt="Button Image">\n    </button>',
                    "xpath": '//html/body/button[@id="image-button"]',
                    "elementText": None,
                    "textNodeIndex": None,
                    "idSymbol": "$",
                    "idString": "[ $ 0 ]",
                },
            ],
            [],
        ),
        (
            "image_and_text.html",
            [
                {
                    "tarsierID": 0,
                    "elementName": "img",
                    "elementHTML": '<img src="https://placehold.co/200x200?text=`" alt="An image" style="float: left; margin-right: 10px">',
                    "xpath": "//html/body/div/img",
                    "elementText": None,
                    "textNodeIndex": None,
                    "idSymbol": "%",
                    "idString": "[ % 0 ]",
                },
                {
                    "tarsierID": 1,
                    "elementName": "p",
                    "elementHTML": "<p>Some text next to an image</p>",
                    "xpath": "//html/body/div/p",
                    "elementText": "Some text next to an image",
                    "textNodeIndex": 1,
                    "idSymbol": "",
                    "idString": "[ 1 ]",
                },
            ],
            ["Some text next to an image"],
        ),
        (
            "different_image_sizes.html",
            [
                {
                    "tarsierID": 0,
                    "elementName": "img",
                    "elementHTML": '<img id="small" src="https://placehold.co/60x60?text=+" alt="Small Image">',
                    "xpath": '//html/body/img[1][@id="small"]',
                    "elementText": None,
                    "textNodeIndex": None,
                    "idSymbol": "%",
                    "idString": "[ % 0 ]",
                },
                {
                    "tarsierID": 1,
                    "elementName": "img",
                    "elementHTML": '<img id="medium" src="https://placehold.co/250x250?text=+" alt="Medium Image">',
                    "xpath": '//html/body/img[2][@id="medium"]',
                    "elementText": None,
                    "textNodeIndex": None,
                    "idSymbol": "%",
                    "idString": "[ % 1 ]",
                },
                {
                    "tarsierID": 2,
                    "elementName": "img",
                    "elementHTML": '<img id="large" src="https://placehold.co/600x600?text=+" alt="Large Image">',
                    "xpath": '//html/body/img[3][@id="large"]',
                    "elementText": None,
                    "textNodeIndex": None,
                    "idSymbol": "%",
                    "idString": "[ % 2 ]",
                },
            ],
            [],
        ),
        (
            "hidden_image.html",
            [
                {
                    "tarsierID": 0,
                    "elementName": "img",
                    "elementHTML": '<img src="https://placehold.co/100x100?text=+" alt="Visible Image" class="visible" id="visible-image">',
                    "xpath": '//html/body/img[1][@id="visible-image"]',
                    "elementText": None,
                    "textNodeIndex": None,
                    "idSymbol": "%",
                    "idString": "[ % 0 ]",
                },
            ],
            [],
        ),
        (
            "image_inside_link.html",
            [
                {
                    "tarsierID": 0,
                    "elementName": "a",
                    "elementHTML": (
                        '<a href="http://example.com" id="link1">\n'
                        '      <img src="https://placehold.co/100x100?text=\'" alt="Linked Image" '
                        'id="image1">\n'
                        "    </a>"
                    ),
                    "xpath": '//html/body/a[@id="link1"]',
                    "elementText": None,
                    "textNodeIndex": None,
                    "idSymbol": "@",
                    "idString": "[ @ 0 ]",
                },
            ],
            [],
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
            tarsier_id = expected_values["tarsierID"]
            matching_tag = next(
                (tag for tag in tag_metadata_list if tag.tarsierID == tarsier_id), None
            )
            assert (
                matching_tag
            ), f"Tag with tarsierID '{tarsier_id}' not found in tag_metadata_list"

            for key, expected_value in expected_values.items():
                actual_value = getattr(matching_tag, key, None)
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
            v["idString"] for v in expected_tag_metadata if "idString" in v
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
            xpath = tag_metadata.xpath
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
