import asyncio
import os
from pathlib import Path
from typing import Dict

from bananalyzer import Example
from bananalyzer.data.examples import get_training_examples
from dotenv import load_dotenv
from playwright.async_api import Browser, async_playwright

from tarsier import GoogleVisionOCRService, Tarsier

load_dotenv()


def google_creds() -> Dict[str, str]:
    return {
        "type": os.getenv("TYPE") or "",
        "project_id": os.getenv("PROJECT_ID") or "",
        "private_key_id": os.getenv("PRIVATE_KEY_ID") or "",
        "private_key": (os.getenv("PRIVATE_KEY") or "").replace("\\n", "\n"),
        "client_email": os.getenv("CLIENT_EMAIL") or "",
        "client_id": os.getenv("CLIENT_ID") or "",
        "auth_uri": os.getenv("AUTH_URI") or "",
        "token_uri": os.getenv("TOKEN_URI") or "",
        "auth_provider_x509_cert_url": os.getenv("AUTH_PROVIDER_X509_CERT_URL") or "",
        "client_x509_cert_url": os.getenv("CLIENT_X509_CERT_URL") or "",
        "universe_domain": os.getenv("UNIVERSE_DOMAIN") or "",
    }


examples = get_training_examples()


async def snapshot_example(
    index: int,
    semaphore: asyncio.Semaphore,
    browser: Browser,
    example: Example,
    snapshots_path: Path,
    tarsier: Tarsier,
) -> None:
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


async def generate_snapshots() -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        snapshots_path = Path(__file__).parent.parent / "snapshots"
        tarsier = Tarsier(GoogleVisionOCRService(google_creds()))
        semaphore = asyncio.Semaphore(10)

        tasks = [
            snapshot_example(i, semaphore, browser, example, snapshots_path, tarsier)
            for i, example in enumerate(examples)
            if example.source == "mhtml"
        ]
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(generate_snapshots())
