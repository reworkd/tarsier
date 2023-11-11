import argparse
import asyncio
import json
from pprint import pprint

from playwright.async_api import async_playwright

from tarsier.core import Tarsier
from tarsier.ocr import GoogleVisionOCRService


async def main(credentials_path: str, url: str, verbose: bool) -> None:
    with open(credentials_path, "r") as f:
        credentials = json.load(f)

    ocr_service = GoogleVisionOCRService(credentials)
    tarsier = Tarsier(ocr_service)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto(url)

        print("👀  Navigated to page.")
        print("🤖  Running Tarsier OCR...")

        page_text, tag_to_xpath = await tarsier.page_to_text(page)

        if verbose:
            print("XPaths:")
            pprint(tag_to_xpath)

        print("Page Text:")
        print(page_text)
        print("✅  Successfully OCR'd page text.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Tarsier OCR command line interface.")
    parser.add_argument(
        "credentials_path", help="Path to the Google credentials JSON file", type=str
    )
    parser.add_argument("url", help="URL to navigate to", type=str)
    parser.add_argument(
        "-v",
        "--verbose",
        help="Show verbose output (including xpaths)",
        action="store_true",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(main(args.credentials_path, args.url, args.verbose))
