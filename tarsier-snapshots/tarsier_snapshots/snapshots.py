import asyncio
import os
from pathlib import Path
from statistics import median
from typing import Dict

from bananalyzer import Example
from bananalyzer.data.examples import get_training_examples
from dotenv import load_dotenv
from numpy import percentile
from playwright.async_api import Browser, async_playwright
from tiktoken import get_encoding

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


class Cl100kBaseTokenCounter:
    def __init__(self) -> None:
        self.encoding = get_encoding("cl100k_base")

    def count(self, text: str) -> int:
        return len(self.tokenize(text))

    def tokenize(self, text: str) -> list[int]:
        return self.encoding.encode(text)


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
        counter = Cl100kBaseTokenCounter()
        # Viewport used in Harambe
        page = await browser.new_page(viewport={"width": 1440, "height": 1024})
        example_path = snapshots_path / example.id
        prefix = f"#{index}/{len(examples)}"
        print(f"{prefix} Snapshotting {example.id}")
        await page.goto(example.get_static_url())
        await page.wait_for_timeout(3000)
        image, _ = await tarsier.page_to_image(page, tag_text_elements=True)
        # page_text, _ = await tarsier.page_to_text(page, tag_text_elements=True)
        page_text_colour_tagged, _ = await tarsier.page_to_text_colour_tag(
            page, tag_text_elements=True
        )
        await page.close()

        # Create the directory if it doesn't exist
        example_path.mkdir(parents=True, exist_ok=True)

        with open(example_path / "screenshot.png", "wb") as f:
            f.write(image)
            print(f"{prefix} Writing screenshot to {example_path / 'screenshot.png'}")

        with open(example_path / "ocr.txt", "w") as f:
            page_text_with_token_count = (
                page_text_colour_tagged
                + f"\nToken count: {counter.count(page_text_colour_tagged)}"
            )
            f.write(page_text_with_token_count)
            print(f"{prefix} Writing OCR text to {example_path / 'ocr.txt'}")
        print(f"{prefix} Finished snapshotting {example.id}")


snapshots_path = Path(__file__).parent.parent / "snapshots"


async def generate_snapshots() -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        tarsier = Tarsier(GoogleVisionOCRService(google_creds()))
        semaphore = asyncio.Semaphore(10)

        tasks = [
            snapshot_example(i, semaphore, browser, example, snapshots_path, tarsier)
            for i, example in enumerate(examples)
            if example.source == "mhtml"
            # if example.source == "mhtml" and example.id == "CsjbrXOwtX1rRqggZALRB"
        ]
        await asyncio.gather(*tasks)


def calculate_token_count_statistics(snapshots_dir: Path) -> None:
    token_counts = []

    print(f"Calculating token count statistics for {snapshots_dir}")
    for file in snapshots_dir.glob("**/ocr.txt"):
        with open(file, "r") as f:
            lines = f.readlines()
            token_count = int(lines[-1].split(":")[-1].strip())
            token_counts.append(token_count)

    statistics = {
        "Min tokens": min(token_counts),
        "Max tokens": max(token_counts),
        "Average tokens": sum(token_counts) / len(token_counts),
        "Median tokens": median(token_counts),
        "p50": percentile(token_counts, 50),
        "p90": percentile(token_counts, 90),
        "p99": percentile(token_counts, 99),
    }

    snapshots_dir = Path(__file__).parent.parent / "snapshots"

    with open(snapshots_dir / "token_statistics.txt", "w") as f:
        print("Writing token count statistics to token_statistics.txt")
        for key, value in statistics.items():
            f.write(f"{key}: {value}\n")


if __name__ == "__main__":
    asyncio.run(generate_snapshots())
    calculate_token_count_statistics(snapshots_path)
