<p align="center">
  <img src="https://raw.githubusercontent.com/reworkd/Tarsier/main/.github/assets/tarsier.png" height="300" alt="Tarsier Monkey" />
</p>
<p align="center">
  <em>🙈 Vision utilities for web interaction agents 🙈</em>
</p>
<p align="center">
    <a href="https://pypi.org/project/tarsier/" target="_blank">
        <img alt="Python" src="https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54" />
        <img alt="Version" src="https://img.shields.io/pypi/v/tarsier?style=for-the-badge&color=3670A0">
    </a>
</p>
<p align="center">
<a href="https://reworkd.ai/">🔗 Main site</a>
<span>&nbsp;&nbsp;•&nbsp;&nbsp;</span>
<a href="https://twitter.com/khoomeik/status/1723432848739483976">🐦 Twitter</a>
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
The video below demonstrates Tarsier usage by feeding a page snapshot into a langchain agent and letting it take actions.

https://github.com/reworkd/tarsier/assets/50181239/af12beda-89b5-4add-b888-d780b353304b

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

Visit our [cookbook](https://github.com/reworkd/Tarsier/tree/main/cookbook) for agent examples using Tarsier:

- [An autonomous LangChain web agent](https://github.com/reworkd/tarsier/blob/main/cookbook/langchain-web-agent.ipynb) 🦜⛓️
- [An autonomous LlamaIndex web agent](https://github.com/reworkd/tarsier/blob/main/cookbook/llama-index-web-agent.ipynb) 🦙

Otherwise, basic Tarsier usage might look like the following:

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

        page_text, tag_to_xpath = await tarsier.page_to_text(page)

        print(tag_to_xpath)  # Mapping of tags to x_paths
        print(page_text)  # My Text representation of the page


if __name__ == '__main__':
    asyncio.run(main())
```

Keep in mind that Tarsier tags different types of elements differently to help your LLM identify what actions are performable on each element. Specifically:
- `[#ID]`: text-insertable fields (e.g. `textarea`, `input` with textual type)
- `[@ID]`: hyperlinks (`<a>` tags)
- `[$ID]`: other interactable elements (e.g. `button`, `select`)
- `[ID]`: plain text (if you pass `tag_text_elements=True`)

## Local Development

### Setup

We have provided a handy setup script to get you up and running with Tarsier development.

```shell
./script/setup.sh
```

If you modify any TypeScript files used by Tarsier, you'll need to execute the following command.
This compiles the TypeScript into JavaScript, which can then be utilized in the Python package.

```shell
npm run build
```

### Testing

We use [pytest](https://docs.pytest.org) for testing. To run the tests, simply run:

```shell
poetry run pytest .
```

### Linting

Prior to submitting a potential PR, please run the following to format your code:

```shell
./script/format.sh
```

## Supported OCR Services

- [x] [Google Cloud Vision](https://cloud.google.com/vision)
- [ ] [Amazon Textract](https://aws.amazon.com/textract/) (Coming Soon)
- [ ] [Microsoft Azure Computer Vision](https://azure.microsoft.com/en-us/services/cognitive-services/computer-vision/) (Coming Soon)

## Roadmap

- [x] Add documentation and examples
- [x] Clean up interfaces and add unit tests
- [x] Launch
- [ ] Improve OCR text performance
- [ ] Add options to customize tagging styling
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
  url          = {https://github.com/reworkd/tarsier}
}
```
