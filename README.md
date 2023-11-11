<p align="center">
  <img src="https://raw.githubusercontent.com/reworkd/Tarsier/main/.github/assets/tarsier.png" height="300" alt="Tarsier Monkey" />
</p>
<p align="center">
  <em>🙈 Vision utilities for web interaction agents 🙈</em>
</p>
<p align="center">
    <img alt="Python" src="https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54" />
</p>
<p align="center">
<a href="https://reworkd.ai/">🔗 Main site</a>
<span>&nbsp;&nbsp;•&nbsp;&nbsp;</span>
<a href="https://twitter.com/reworkdai">🐦 Twitter</a>
<span>&nbsp;&nbsp;•&nbsp;&nbsp;</span>
<a href="https://discord.gg/gcmNyAAFfV">📢 Discord</a>
</p>

# Tarsier
If you've tried using GPT-4(V) to automate web interactions, you've probably run into questions like:
- How do you map LLM responses back into web elements?
- How can you mark up a page for an LLM better understand its action space?
- How do you feed a "screenshot" to a text-only LLM?

At Reworkd, we found ourselves reusing the same utility libraries to solve these problems across multiple projects. 
Because of this we're now open-sourcing this simple utility library for multimodal web agents... Tarsier!

## How does it work?
Tarsier works by visually "tagging" interactable elements on a page via brackets + an id such as `[1]`.
In doing this, we provide a mapping between elements and ids for GPT-4(V) to take actions upon. 
We define interactable elements as buttons, links, or input fields that are visible on the page.

Can provide a textual representation of the page. This means that Tarsier enables deeper interaction for even non multi-modal LLMs.
This is important to note given performance issues with existing vision language models.
Tarsier also provides OCR utils to convert a page screenshot into a whitespace-structured string that an LLM without vision can understand.

## Installation
```shell
pip install tarsier
```

## Usage
An agent using Tarsier might look like this:
```python
import asyncio

from playwright.async_api import async_playwright
from tarsier import Tarsier, GoogleVisionOCRService

async def main():
    google_cloud_credentials = {}

    ocr_service = GoogleVisionOCRService(google_cloud_credentials)
    tarsier = Tarsier(ocr_service)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto("https://news.ycombinator.com")

        driver = tarsier.create_driver(page)
        page_text, tag_to_xpath = await tarsier.page_to_text(driver)

        print(tag_to_xpath)  # Mapping of tags to x_paths
        print(page_text)  # My Text representation of the page


if __name__ == '__main__':
    asyncio.run(main())
```

Visit our [cookbook](https://github.com/reworkd/Tarsier/tree/main/cookbook) for additional examples:
- A LangChain web agent
- A LlamaIndex web agent

## Roadmap
- [x] Add documentation and examples
- [x] Clean up interfaces and add unit tests
- [x] Launch


- [ ] Improve OCR text performance
- [ ] Add options to customize tagging
- [ ] Add support for other browsers drivers as necessary
- [ ] Add support for other OCR services as necessary

## Citations
```
bibtex
@misc{reworkd2023tarsier,
  title        = {Tarsier},
  author       = {Rohan Pandey and Adam Watkins and Asim Shrestha and Srijan Subedi},
  year         = {2023},
  howpublished = {GitHub},
  url          = {https://github.com/reworkd/bananalyzer}
}
```
