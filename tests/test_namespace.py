import os

import pytest
import pytest_asyncio
from playwright.async_api import Page

from tarsier import Tarsier, DummyOCRService
from tarsier.adapter import adapter_factory, BrowserAdapter


@pytest_asyncio.fixture()
async def browser_adapter_with_js(async_page: Page) -> BrowserAdapter:
    tarsier = Tarsier(DummyOCRService())
    adapter = adapter_factory(async_page)
    await tarsier._load_tarsier_utils(adapter)
    return adapter


@pytest.mark.asyncio
async def test_fix_namespaces(browser_adapter_with_js):
    # Manually define test cases to avoid recreating page for each test
    # There are some issues with changing the playwright page fixtures to remain the same for the session/module
    test_cases = [
        # Basic namespaced tags
        ("a:b", '*[name()="a:b"]'),
        ("foo:bar", '*[name()="foo:bar"]'),
        # Non-namespaced tags
        ("div", "div"),
        ("span", "span"),
        # Tags with IDs and classes (no namespaces)
        ("div#main-content", "div#main-content"),
        ("span.highlighted", "span.highlighted"),
        # Namespaced tags with IDs and classes
        ("ns:div#main-content", '*[name()="ns:div"]#main-content'),
        ("xhtml:span.highlighted", '*[name()="xhtml:span"].highlighted'),
        # Tags with multiple classes (no namespaces)
        ("div.class1.class2", "div.class1.class2"),
        # Namespaced tag with attributes and classes
        (
            "svg:rect#my-rect.class1.class2",
            '*[name()="svg:rect"]#my-rect.class1.class2',
        ),
        # Complex cases with IDs and classes
        ("html:div#id1.class1.class2", '*[name()="html:div"]#id1.class1.class2'),
        ("math:mi#identifier.symbol", '*[name()="math:mi"]#identifier.symbol'),
        # Tag name resembling a namespace (but isn't one)
        ("div:class", '*[name()="div:class"]'),
        ("ns3:div.class1", '*[name()="ns3:div"].class1'),
    ]

    for value in test_cases:
        input_tag, expected_output = value
        result = await browser_adapter_with_js.run_js(
            f"window.fixNamespaces('{input_tag}')"
        )

        assert (
            result == expected_output
        ), f"For {input_tag}, expected {expected_output} but got {result}"


@pytest.mark.asyncio
async def test_xpath_namespace(tarsier, async_page):
    html_with_namespace_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "mock_html/namespace.html")
    )
    await async_page.goto(f"file://{html_with_namespace_path}")

    _, tag_to_xpath = await tarsier.page_to_text(async_page, tag_text_elements=True)
    assert len(tag_to_xpath) == 1, "The page contains only a single tag"
    assert (
        tag_to_xpath[0] == '//html/body/*[name()="sc:visitoridentification"]/div/text()'
    ), f"Namespaces within the xpath were not correctly handled " f"Got: {tag_to_xpath}"
