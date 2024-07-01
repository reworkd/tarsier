import os
import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "html_file, expected_tag_to_xpath",
    [
        ("mock_html/text_only.html", {0: "//html/body/h1", 1: "//html/body/p"}),
        (
            "mock_html/hyperlink_only.html",
            {0: '//html/body/p/a[@id="link1"]'},
        ),
        (
            "mock_html/interactable_only.html",
            {
                0: '//html/body/form/button[@id="button"]',
                1: '//html/body/form/input[@id="checkbox"]',
            },
        ),
        (
            "mock_html/combination.html",
            {
                0: "//html/body/h1",
                1: "//html/body/p[1]",
                2: "//html/body/form/label[1]",
                3: '//html/body/form/input[1][@id="text"]',
                4: "//html/body/form/label[2]",
                5: '//html/body/form/input[2][@id="checkbox"]',
                6: "//html/body/form/label[3]",
                7: '//html/body/form/input[3][@id="radio1"]',
                8: "//html/body/form/label[4]",
                9: '//html/body/form/input[4][@id="radio2"]',
                10: "//html/body/form/label[5]",
                11: '//html/body/form/select[@id="select"]',
                12: "//html/body/form/label[6]",
                13: '//html/body/form/input[5][@id="file"]',
                14: '//html/body/p[2]/a[@id="link1"]',
            },
        ),
        (
            "mock_html/insertable_only.html",
            {
                0: '//html/body/form/input[1][@id="text"]',
                1: '//html/body/form/input[2][@id="password"]',
            },
        ),
    ],
)
async def test_combined_elements_page(
    tarsier, async_page, html_file, expected_tag_to_xpath
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

    num_lines = len(page_text.splitlines())

    if "combination.html" not in html_file:
        assert 2 < num_lines < 6, (
            f"Number of lines in page_text does not meet the criteria for "
            f"{html_file}. Got: {num_lines} lines."
        )
    else:
        assert 9 < num_lines < 13, (
            f"Number of lines in page_text does not meet the criteria for "
            f"{html_file}. Got: {num_lines} lines."
        )
