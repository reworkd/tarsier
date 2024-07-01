import json
import os
from os import environ

import pytest
import pytest_asyncio
from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

from tarsier import GoogleVisionOCRService, Tarsier, MicrosoftAzureOCRService
from dotenv import load_dotenv

load_dotenv()
IN_GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"


@pytest_asyncio.fixture()
async def browser() -> None:
    async with async_playwright() as pw:
        pw_browser = await pw.chromium.launch(headless=IN_GITHUB_ACTIONS)
        yield pw_browser
        await pw_browser.close()


@pytest_asyncio.fixture()
async def context(browser) -> None:
    pw_context = await browser.new_context()
    yield pw_context
    await pw_context.close()


@pytest_asyncio.fixture()
async def async_page(context) -> None:
    page = await context.new_page()
    yield page
    await page.close()


@pytest.fixture()
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


@pytest.fixture(params=["microsoft", "google"])
def credentials(request):
    provider: str = request.param
    env_variable = f"TARSIER_{provider.upper()}_OCR_CREDENTIALS"

    if not (creds := environ.get(env_variable, None)):
        raise Exception(f"Please set the {env_variable}  environment variable.")

    return provider, json.loads(creds)


@pytest.fixture
def tarsier(credentials):
    provider, credentials = credentials

    match provider:
        case "microsoft":
            ocr_service = MicrosoftAzureOCRService(credentials)
        case "google":
            ocr_service = GoogleVisionOCRService(credentials)
        case _:
            raise ValueError("Invalid OCR provider")

    yield Tarsier(ocr_service)
