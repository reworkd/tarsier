import asyncio
import json
import os
from os import environ

import nest_asyncio
import pytest
import pytest_asyncio
from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

from tarsier import GoogleVisionOCRService, Tarsier

IN_GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"


@pytest.fixture(scope="module")
@pytest.mark.asyncio
def event_loop():
    nest_asyncio.apply()
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="module")
@pytest.mark.asyncio
async def async_page() -> None:
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=IN_GITHUB_ACTIONS)
        page = await browser.new_page()
        yield page
        await browser.close()


@pytest.fixture(scope="module")
def sync_page() -> None:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=IN_GITHUB_ACTIONS)
        page = browser.new_page()
        yield page
        browser.close()


@pytest.fixture
def chrome_driver():
    options = webdriver.ChromeOptions()
    if IN_GITHUB_ACTIONS:
        options.add_argument("headless")

    path = ChromeDriverManager().install()
    driver = webdriver.Chrome(service=ChromeService(path), options=options)

    yield driver

    driver.quit()


@pytest.fixture
def tarsier():
    if not (creds := environ.get("TARSIER_GOOGLE_OCR_CREDENTIALS", None)):
        raise Exception(
            "Please set the TARSIER_GOOGLE_OCR_CREDENTIALS environment variable."
        )

    credentials = json.loads(creds)
    ocr_service = GoogleVisionOCRService(credentials)
    yield Tarsier(ocr_service)
