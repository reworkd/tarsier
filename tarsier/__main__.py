import argparse
import asyncio
import json
from pprint import pprint

from playwright.async_api import async_playwright

from tarsier.core import Tarsier
from tarsier.ocr import GoogleVisionOCRService, MicrosoftAzureOCRService
from tarsier.ocr.ocr_service import OCRProvider, OCRService


async def main(
    credentials_path: str, url: str, verbose: bool, ocr_provider: OCRProvider = "google"
) -> None:
    with open(credentials_path, "r") as f:
        credentials = json.load(f)

    ocr_service: OCRService
    match ocr_provider:
        case "google":
            ocr_service = GoogleVisionOCRService(credentials)

        case "microsoft":
            ocr_service = MicrosoftAzureOCRService(credentials)

        case _:
            raise Exception(
                "Unknown OCR Provider. Please select one of the available OCR providers."
            )

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
        "credentials_path", help="Path to the OCR credentials JSON file", type=str
    )
    parser.add_argument("url", help="URL to navigate to", type=str)
    parser.add_argument(
        "-v",
        "--verbose",
        help="Show verbose output (including xpaths)",
        action="store_true",
    )
    parser.add_argument(
        "--ocr_provider",
        help="Which OCR service to use [google, microsoft]",
        type=str,
        required=False,
        default="google",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(main(args.credentials_path, args.url, args.verbose, args.ocr_provider))
