import os
import pytest


@pytest.mark.asyncio
async def test_fixNamespaces(browser_adapter_with_js):
    input_xpath = "/a:b/c:d"
    expected_output = '/*[name()="a:b"]/*[name()="c:d"]'

    result = await browser_adapter_with_js.run_js(f"fixNamespaces('{input_xpath}')")

    assert (
        result == expected_output
    ), f"For {input_xpath}, expected {expected_output} but got {result}"


@pytest.mark.asyncio
async def test_fixNamespaces_no_namespace(browser_adapter_with_js):
    input_xpath = "/without_namespace"
    expected_output = "/without_namespace"

    result = await browser_adapter_with_js.run_js(f"fixNamespaces('{input_xpath}')")

    assert (
        result == expected_output
    ), f"For {input_xpath}, expected {expected_output} but got {result}"


@pytest.mark.asyncio
async def test_fixNamespaces_multiple_namespaces(browser_adapter_with_js):
    input_xpath = "/foo:bar/baz:qux"
    expected_output = '/*[name()="foo:bar"]/*[name()="baz:qux"]'

    result = await browser_adapter_with_js.run_js(f"fixNamespaces('{input_xpath}')")

    assert (
        result == expected_output
    ), f"For {input_xpath}, expected {expected_output} but got {result}"


@pytest.mark.asyncio
async def test_xpath_namespace(tarsier, async_page):
    html_file = "mock_html/namespace.html"
    expected_xpath = '//html/body/*[name()="sc:visitoridentification"]/div'

    html_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), html_file))
    await async_page.goto(f"file://{html_file_path}")

    page_text, tag_to_xpath = await tarsier.page_to_text(
        async_page, tag_text_elements=True
    )
    assert tag_to_xpath[0] == expected_xpath, (
        f"tag_to_xpath does not match expected xpath. Namespace may not have been handled correctly."
        f"Expected {expected_xpath}. Got: {tag_to_xpath[0]}"
    )
