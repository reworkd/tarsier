import asyncio
import json
from os import environ

import nest_asyncio
import pytest
import pytest_asyncio
from playwright.async_api import async_playwright

from tarsier import GoogleVisionOCRService, Tarsier


@pytest.fixture(scope="module")
def event_loop():
    nest_asyncio.apply()
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="module")
@pytest.mark.asyncio
async def async_page() -> None:
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        page = await browser.new_page()
        yield page
        await browser.close()


@pytest.fixture
def tarsier():
    if not (creds := environ.get("TARSIER_GOOGLE_OCR_CREDENTIALS", None)):
        raise Exception("Please set the TARSIER_GOOGLE_OCR_CREDENTIALS environment variable.")

    credentials = json.loads(creds)
    ocr_service = GoogleVisionOCRService(credentials)
    yield Tarsier(ocr_service)

