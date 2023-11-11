import asyncio

import nest_asyncio
import pytest
import pytest_asyncio
from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

from tarsier import GoogleVisionOCRService, Tarsier


@pytest.fixture(scope="module")
def event_loop():
    nest_asyncio.apply()
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="module")
@pytest.mark.asyncio
async def async_page() -> None:
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        page = await browser.new_page()
        yield page
        await browser.close()


@pytest.fixture(scope="module")
def sync_page() -> None:
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        yield page
        browser.close()


@pytest.fixture
def chrome_driver():
    options = webdriver.ChromeOptions()
    # options.add_argument('headless')

    path = ChromeDriverManager().install()
    driver = webdriver.Chrome(service=ChromeService(path), options=options)

    yield driver

    driver.quit()


@pytest.fixture
def tarsier():
    # if not (creds := environ.get("TARSIER_GOOGLE_OCR_CREDENTIALS", None)):
    #     raise Exception("Please set the TARSIER_GOOGLE_OCR_CREDENTIALS environment variable.")
    # creds = '{"type": "service_account", "project_id": "llama-2d", "private_key_id": "49339af46b6e01c01cba6277dcf0e3beeb63e871", "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCKBeT3UeP+X2bz\n60OAMoQ0qbtbjr0bwfV64IQkH016Jp141OWCtgVTIteEq7BRx3nuoyAhhwOQkq4H\nsB0ZvXsTfwh9Rg1LPkmweDQ8C3lg7ky/sp6yX/bNiRYIQxFzP0YFZokGs+Pn17Bc\niAxlJ8K2KuHZjlsHtYuIJ2UsijugoR++Cet+IzbtuQkJenoBGpbBd+4WBMEz5sQB\nkk/R1T47ubVO1TpcgnPYTzamO0TJ9Px1qE1Fb/Wt61ThlZEI3VWiYRCUhwcaZ2fQ\neSY1qJ59yLRl1xRWhSpSThltxDXbqWxRhGjFRUtlagWRYac4bRwLcbQ9T4RreFvc\niXi2hV2jAgMBAAECggEANynN7i7zkYntqtU/gDAweJ/RuvEckch+ZSLwjUNZgtWG\nIHHuXMSE8ko9ms/Hw5eXGxJlWCEPAqwtE/OGXfBGDW+7I95ol8cISphwQANR+rSj\nRgaMuLvz9wewH5M2mToTsTrezyf8kX+6A/F4CsHOZ2JSK9JifX1IjB06qYeB91t3\n8zKxUyHniP/oheZG7Oo50sVHyTVwNkJvykfiRfQJzljtpTyRz+UmHaAWjC6exonC\nppqmCZTub4MeO/dsNkDRs7j8EFDUpUNBfl0cIFqdbqPM4K81e6zeB3eRaEeqKsSW\nHUbQFjqKqp28nmC2E1Ujx7SuXla8YFRS7RjCXQwqAQKBgQDBlPVg7q4XMsGFhBVA\nwXdXSYY3QIXodgvs0u40WvjeaGzKkQ8YI3Qjoev5/SXHBKldXVFky5WBbR9qneZa\nXrl8umrii870wchCmWPwvfoVphnq4knB3SK/MTUG/yw28wqfVOcjZqDxfNkBZ8LR\nLDwV4L2ZZUjqqF2Vt05W6Q/eowKBgQC2huGJmDFgZzjnYT6rIPT1Mu6IRwsD+6Wh\n8DhgkLV/TWoZ27VaGBIEdZ7xNKO8mofYNV05sUAb9DwH1CbDM9IK7A9R0nJ+Zvhj\n+aZck7IJG9nzvapAGdWS7xSgUSAoPy2BmrP9tY/x5+/gZlw0fVGgsuJpVeEkJVyO\nwRp+VMd1AQKBgHIsJdEm1LzP7b2Omm5X7MgpkCR0RMZHIV9rRJzSbufWFRwgFBP7\njRsa/C+0M5y+zhlH2aKmRCZSsu3R9TOlnKbI2BOHu+c1h6RoDb7GfYJZNf4HutLB\nVyYGoqzewTgjfkdc7vo9JH1pUh/3D7sI6ONKaujXCPuFk7SiqWyvBvIbAoGAUOYR\nWoHJCLhXYT4Zn5F44KCVVnNeb4J+k/q7khkxSF4Qc6uMgoT+n1lee/vfwn0fTnXA\nfwyPpJQoczPVhlkWdF7SH2rN8jZDS1RgJtITa7QbcsuShNyua3RpyPCL9yqhSbs+\noWlyhj5NdEEKBv2wSzBd51/37KRelKsDyhBbYwECgYAWwqarv9enHdSfgpCQUp7T\nZuGfa6g2xK+UHsKMvh91EThMnpWGDqO8CfRS0e4FHVi7d9aY1FTu+f8ZFocPzI3J\nSTAqjDFMaDV4exlbJL2XJtis5sfRlJ52jgfEnwi10FNM0W2MO2fsFnv1FguNeGa8\nMDR1a70ibABN52KICn/aMA==\n-----END PRIVATE KEY-----\n", "client_email": "ocr-service1@llama-2d.iam.gserviceaccount.com", "client_id": "116100767100188078734", "auth_uri": "https://accounts.google.com/o/oauth2/auth", "token_uri": "https://oauth2.googleapis.com/token", "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs", "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/ocr-service1%40llama-2d.iam.gserviceaccount.com", "universe_domain": "googleapis.com"}'
    # credentials = json.loads(creds)

    credentials = {
        "type": "service_account",
        "project_id": "llama-2d",
        "private_key_id": "49339af46b6e01c01cba6277dcf0e3beeb63e871",
        "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCKBeT3UeP+X2bz\n60OAMoQ0qbtbjr0bwfV64IQkH016Jp141OWCtgVTIteEq7BRx3nuoyAhhwOQkq4H\nsB0ZvXsTfwh9Rg1LPkmweDQ8C3lg7ky/sp6yX/bNiRYIQxFzP0YFZokGs+Pn17Bc\niAxlJ8K2KuHZjlsHtYuIJ2UsijugoR++Cet+IzbtuQkJenoBGpbBd+4WBMEz5sQB\nkk/R1T47ubVO1TpcgnPYTzamO0TJ9Px1qE1Fb/Wt61ThlZEI3VWiYRCUhwcaZ2fQ\neSY1qJ59yLRl1xRWhSpSThltxDXbqWxRhGjFRUtlagWRYac4bRwLcbQ9T4RreFvc\niXi2hV2jAgMBAAECggEANynN7i7zkYntqtU/gDAweJ/RuvEckch+ZSLwjUNZgtWG\nIHHuXMSE8ko9ms/Hw5eXGxJlWCEPAqwtE/OGXfBGDW+7I95ol8cISphwQANR+rSj\nRgaMuLvz9wewH5M2mToTsTrezyf8kX+6A/F4CsHOZ2JSK9JifX1IjB06qYeB91t3\n8zKxUyHniP/oheZG7Oo50sVHyTVwNkJvykfiRfQJzljtpTyRz+UmHaAWjC6exonC\nppqmCZTub4MeO/dsNkDRs7j8EFDUpUNBfl0cIFqdbqPM4K81e6zeB3eRaEeqKsSW\nHUbQFjqKqp28nmC2E1Ujx7SuXla8YFRS7RjCXQwqAQKBgQDBlPVg7q4XMsGFhBVA\nwXdXSYY3QIXodgvs0u40WvjeaGzKkQ8YI3Qjoev5/SXHBKldXVFky5WBbR9qneZa\nXrl8umrii870wchCmWPwvfoVphnq4knB3SK/MTUG/yw28wqfVOcjZqDxfNkBZ8LR\nLDwV4L2ZZUjqqF2Vt05W6Q/eowKBgQC2huGJmDFgZzjnYT6rIPT1Mu6IRwsD+6Wh\n8DhgkLV/TWoZ27VaGBIEdZ7xNKO8mofYNV05sUAb9DwH1CbDM9IK7A9R0nJ+Zvhj\n+aZck7IJG9nzvapAGdWS7xSgUSAoPy2BmrP9tY/x5+/gZlw0fVGgsuJpVeEkJVyO\nwRp+VMd1AQKBgHIsJdEm1LzP7b2Omm5X7MgpkCR0RMZHIV9rRJzSbufWFRwgFBP7\njRsa/C+0M5y+zhlH2aKmRCZSsu3R9TOlnKbI2BOHu+c1h6RoDb7GfYJZNf4HutLB\nVyYGoqzewTgjfkdc7vo9JH1pUh/3D7sI6ONKaujXCPuFk7SiqWyvBvIbAoGAUOYR\nWoHJCLhXYT4Zn5F44KCVVnNeb4J+k/q7khkxSF4Qc6uMgoT+n1lee/vfwn0fTnXA\nfwyPpJQoczPVhlkWdF7SH2rN8jZDS1RgJtITa7QbcsuShNyua3RpyPCL9yqhSbs+\noWlyhj5NdEEKBv2wSzBd51/37KRelKsDyhBbYwECgYAWwqarv9enHdSfgpCQUp7T\nZuGfa6g2xK+UHsKMvh91EThMnpWGDqO8CfRS0e4FHVi7d9aY1FTu+f8ZFocPzI3J\nSTAqjDFMaDV4exlbJL2XJtis5sfRlJ52jgfEnwi10FNM0W2MO2fsFnv1FguNeGa8\nMDR1a70ibABN52KICn/aMA==\n-----END PRIVATE KEY-----\n",
        "client_email": "ocr-service1@llama-2d.iam.gserviceaccount.com",
        "client_id": "116100767100188078734",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/ocr-service1%40llama-2d.iam.gserviceaccount.com",
        "universe_domain": "googleapis.com",
    }
    ocr_service = GoogleVisionOCRService(credentials)
    yield Tarsier(ocr_service)
