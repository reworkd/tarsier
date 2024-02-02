import asyncio
import os
from pathlib import Path

from bananalyzer.data.examples import get_training_examples
from dotenv import load_dotenv
from playwright.async_api import async_playwright

from tarsier import Tarsier, GoogleVisionOCRService

load_dotenv()


def google_creds() -> dict:
    return {
        "type": os.getenv("TYPE"),
        "project_id": os.getenv("PROJECT_ID"),
        "private_key_id": os.getenv("PRIVATE_KEY_ID"),
        "private_key": os.getenv("PRIVATE_KEY").replace("\\n", "\n"),
        "client_email": os.getenv("CLIENT_EMAIL"),
        "client_id": os.getenv("CLIENT_ID"),
        "auth_uri": os.getenv("AUTH_URI"),
        "token_uri": os.getenv("TOKEN_URI"),
        "auth_provider_x509_cert_url": os.getenv("AUTH_PROVIDER_X509_CERT_URL"),
        "client_x509_cert_url": os.getenv("CLIENT_X509_CERT_URL"),
        "universe_domain": os.getenv("UNIVERSE_DOMAIN"),
    }


examples = get_training_examples()


async def snapshot_example(index: int, semaphore: asyncio.Semaphore, browser, example, snapshots_path, tarsier):
    async with semaphore:
        page = await browser.new_page()
        example_path = snapshots_path / example.id
        print(f"#{index}/{len(examples)} Snapshotting {example.id}")
        await page.goto(example.get_static_url())
        image, _ = await tarsier.page_to_image(page, tag_text_elements=True)
        page_text, _ = await tarsier.page_to_text(page, tag_text_elements=True)
        await page.close()

        # Create the directory if it doesn't exist
        example_path.mkdir(parents=True, exist_ok=True)

        with open(example_path / "screenshot.png", "wb") as f:
            f.write(image)
            print(f"Writing screenshot to {example_path / 'screenshot.png'}")

        with open(example_path / "ocr.txt", "w") as f:
            f.write(page_text)
            print(f"Writing OCR text to {example_path / 'ocr.txt'}")
        print(f"Finished snapshotting {example.id}")


async def generate_snapshots():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        snapshots_path = Path(__file__).parent.parent / "snapshots"
        tarsier = Tarsier(GoogleVisionOCRService(google_creds()))
        semaphore = asyncio.Semaphore(10)

        tasks = [
            snapshot_example(i, semaphore, browser, example, snapshots_path, tarsier)
            for i, example in enumerate(examples) if example.source == "mhtml"
        ]
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(generate_snapshots())
