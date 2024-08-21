from playwright.async_api import async_playwright
import os
from tarsier import Tarsier, GoogleVisionOCRService
from dotenv import load_dotenv
import json

load_dotenv() 
def load_ocr_credentials(json_file_path):
    with open(json_file_path) as f:
        credentials = json.load(f)
    return credentials

google_cloud_credentials = load_ocr_credentials('./gcp.json')
ocr_service = GoogleVisionOCRService(google_cloud_credentials)
tarsier = Tarsier(ocr_service)


async def url_to_page_text(url: str):
    
    async with async_playwright() as playwright:
        chromium = playwright.chromium
        browser = await chromium.connect_over_cdp('wss://connect.browserbase.com?apiKey='+ os.environ["DEWORKD_BROWSERBASE_API_KEY"])
        context = browser.contexts[0]
        page = context.pages[0]
        await page.goto(url)
        page_text, tag_to_xpath = await tarsier.page_to_text(page, tagless=True)
        return page_text


# asyncio.run(run())

    



