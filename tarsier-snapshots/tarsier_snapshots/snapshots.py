import asyncio
import os
from pathlib import Path
from statistics import median
from typing import Dict
import time

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
        start_time = time.perf_counter()
        image, _ = await tarsier.page_to_image(page, tag_text_elements=True)
        screenshot_duration = time.perf_counter() - start_time
        start_time = time.perf_counter()
        page_text, _ = await tarsier.page_to_text(page, tag_text_elements=True)
        ocr_duration = time.perf_counter() - start_time
        await page.close()

        # Create the directory if it doesn't exist
        example_path.mkdir(parents=True, exist_ok=True)

        with open(example_path / "screenshot.png", "wb") as f:
            f.write(image)
            print(f"{prefix} Writing screenshot to {example_path / 'screenshot.png'}")

        with open(example_path / "ocr.txt", "w") as f:
            page_text_with_token_count = (
                page_text
                + f"\nImage timing: {screenshot_duration:.2f} seconds"
                + f"\nPage text timing: {ocr_duration:.2f} seconds"
                + f"\nToken count: {counter.count(page_text)}"
            )
            f.write(page_text_with_token_count)
            print(f"{prefix} Writing OCR text to {example_path / 'ocr.txt'}")
        print(f"{prefix} Finished snapshotting {example.id}")


snapshots_path = Path(__file__).parent.parent / "snapshots"


async def generate_snapshots() -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        tarsier = Tarsier(GoogleVisionOCRService(google_creds()))
        semaphore = asyncio.Semaphore(10)

        tasks = [
            snapshot_example(i, semaphore, browser, example, snapshots_path, tarsier)
            for i, example in enumerate(examples)
            if example.source == "mhtml"
            # if example.source == "mhtml" and example.id == "h4q2uwr0z0sVFM0q5AV7n"
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


def calculate_image_timing_statistics(snapshots_dir: Path) -> None:
    screenshot_durations = []

    print(f"Calculating image timing statistics for {snapshots_dir}")
    for file in snapshots_dir.glob("**/ocr.txt"):
        with open(file, "r") as f:
            lines = f.readlines()
            screenshot_duration = float(lines[-3].split(":")[-1].strip().split()[0])
            screenshot_durations.append(screenshot_duration)

    statistics = {
        "Min screenshot duration": min(screenshot_durations),
        "Max screenshot duration": max(screenshot_durations),
        "Average screenshot duration": sum(screenshot_durations) / len(screenshot_durations),
        "Median screenshot duration": median(screenshot_durations),
        "p50 screenshot duration": percentile(screenshot_durations, 50),
        "p90 screenshot duration": percentile(screenshot_durations, 90),
        "p99 screenshot duration": percentile(screenshot_durations, 99),
    }

    snapshots_dir = Path(__file__).parent.parent / "snapshots"

    with open(snapshots_dir / "image_timing_statistics.txt", "w") as f:
        print("Writing image timing statistics to image_timing_statistics.txt")
        for key, value in statistics.items():
            f.write(f"{key}: {value}\n")


def calculate_page_text_timing_statistics(snapshots_dir: Path) -> None:
    ocr_durations = []

    print(f"Calculating page text timing statistics for {snapshots_dir}")
    for file in snapshots_dir.glob("**/ocr.txt"):
        with open(file, "r") as f:
            lines = f.readlines()
            ocr_duration = float(lines[-2].split(":")[-1].strip().split()[0])
            ocr_durations.append(ocr_duration)

    statistics = {
        "Min OCR duration": min(ocr_durations),
        "Max OCR duration": max(ocr_durations),
        "Average OCR duration": sum(ocr_durations) / len(ocr_durations),
        "Median OCR duration": median(ocr_durations),
        "p50 OCR duration": percentile(ocr_durations, 50),
        "p90 OCR duration": percentile(ocr_durations, 90),
        "p99 OCR duration": percentile(ocr_durations, 99),
    }

    snapshots_dir = Path(__file__).parent.parent / "snapshots"

    with open(snapshots_dir / "page_text_timing_statistics.txt", "w") as f:
        print("Writing page text timing statistics to page_text_timing_statistics.txt")
        for key, value in statistics.items():
            f.write(f"{key}: {value}\n")


if __name__ == "__main__":
    asyncio.run(generate_snapshots())
    calculate_image_timing_statistics(snapshots_path)
    calculate_page_text_timing_statistics(snapshots_path)
    calculate_token_count_statistics(snapshots_path)
