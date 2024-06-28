import os
import pytest
from playwright.async_api import async_playwright
from dotenv import load_dotenv
from typing import Dict
from tarsier import GoogleVisionOCRService, Tarsier

dotenv_path = os.path.join(os.path.dirname(__file__), "test.env")
load_dotenv(dotenv_path)


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


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "html_file, expected_tag_to_xpath",
    [
        ("test_html/text_only.html", {0: "//html/body/h1", 1: "//html/body/p"}),
        (
            "test_html/hyperlink_only.html",
            {
                0: '//html/body/p[1]/a[@id="link1"]',
                1: '//html/body/p[2]/a[@id="link2"]',
                2: '//html/body/p[3]/a[@id="link3"]',
                3: '//html/body/p[4]/a[@id="link4"]',
                4: '//html/body/p[5]/a[@id="link5"]',
            },
        ),
        (
            "test_html/interactable_only.html",
            {
                0: '//html/body/form/button[@id="button"]',
                1: '//html/body/form/input[1][@id="checkbox"]',
                2: '//html/body/form/input[2][@id="radio1"]',
                3: '//html/body/form/input[3][@id="radio2"]',
                4: '//html/body/form/select[@id="select"]',
                5: '//html/body/form/input[4][@id="file"]',
            },
        ),
        (
            "test_html/combination.html",
            {
                0: "//html/body/h1",
                1: "//html/body/p[1]",
                2: "//html/body/form/label[1]",
                3: '//html/body/form/input[1][@id="text"]',
                4: "//html/body/form/label[2]",
                5: '//html/body/form/input[2][@id="password"]',
                6: "//html/body/form/label[3]",
                7: '//html/body/form/input[3][@id="email"]',
                8: "//html/body/form/label[4]",
                9: '//html/body/form/input[4][@id="search"]',
                10: "//html/body/form/label[5]",
                11: '//html/body/form/input[5][@id="url"]',
                12: "//html/body/form/label[6]",
                13: '//html/body/form/input[6][@id="tel"]',
                14: "//html/body/form/label[7]",
                15: '//html/body/form/input[7][@id="number"]',
                16: "//html/body/form/label[8]",
                17: '//html/body/form/textarea[@id="textarea"]',
                18: "//html/body/form/label[9]",
                19: '//html/body/form/button[@id="button"]',
                20: "//html/body/form/label[10]",
                21: '//html/body/form/input[8][@id="checkbox"]',
                22: "//html/body/form/label[11]",
                23: '//html/body/form/input[9][@id="radio1"]',
                24: "//html/body/form/label[12]",
                25: '//html/body/form/input[10][@id="radio2"]',
                26: "//html/body/form/label[13]",
                27: '//html/body/form/select[@id="select"]',
                28: "//html/body/form/label[14]",
                29: '//html/body/form/input[11][@id="file"]',
                30: '//html/body/p[2]/a[@id="link1"]',
                31: '//html/body/p[3]/a[@id="link2"]',
                32: '//html/body/p[4]/a[@id="link3"]',
                33: '//html/body/p[5]/a[@id="link4"]',
                34: '//html/body/p[6]/a[@id="link5"]',
            },
        ),
        (
            "test_html/insertable_only.html",
            {
                0: '//html/body/form/input[1][@id="text"]',
                1: '//html/body/form/input[2][@id="password"]',
                2: '//html/body/form/input[3][@id="email"]',
                3: '//html/body/form/input[4][@id="search"]',
                4: '//html/body/form/input[5][@id="url"]',
                5: '//html/body/form/input[6][@id="tel"]',
                6: '//html/body/form/input[7][@id="number"]',
                7: '//html/body/form/textarea[@id="textarea"]',
            },
        ),
    ],
)
async def test_combined_elements_page(html_file, expected_tag_to_xpath):
    async with async_playwright() as p:
        creds = google_creds()

        browser = await p.chromium.launch(headless=True)
        tarsier = Tarsier(GoogleVisionOCRService(creds))

        html_file_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), html_file)
        )
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(f"file://{html_file_path}")

        page_text, tag_to_xpath = await tarsier.page_to_text(
            page, tag_text_elements=True
        )

        assert tag_to_xpath == expected_tag_to_xpath, (
            f"tag_to_xpath does not match expected output for "
            f"{html_file}. Got: {tag_to_xpath}"
        )
