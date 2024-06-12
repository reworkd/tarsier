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

If you've tried using an LLM to automate web interactions, you've probably run into questions like:

- How should you feed the webpage to an LLM? (e.g. HTML, Accessibility Tree, Screenshot)
- How do you map LLM responses back to web elements?
- How can you inform a text-only LLM about the page's visual structure?

At Reworkd, we iterated on all these problems across tens of thousands of real web tasks to build a powerful perception system for web agents... Tarsier!
In the video below, we use Tarsier to provide webpage perception for a minimalistic GPT-4 LangChain web agent.

https://github.com/reworkd/tarsier/assets/50181239/af12beda-89b5-4add-b888-d780b353304b

## How does it work?

Tarsier visually tags interactable elements on a page via brackets + an ID e.g. `[23]`.
In doing this, we provide a mapping between elements and IDs for an LLM to take actions upon (e.g. `CLICK [23]`).
We define interactable elements as buttons, links, or input fields that are visible on the page; Tarsier can also tag all textual elements if you pass `tag_text_elements=True`.

Furthermore, we've developed an OCR algorithm to convert a page screenshot into a whitespace-structured string (almost like ASCII art) that an LLM *even without vision* can understand.
Since current vision-language models still lack fine-grained representations needed for web interaction tasks, this is critical.
On our internal benchmarks, unimodal GPT-4 + Tarsier-Text beats GPT-4V + Tarsier-Screenshot by 10-20%!

Tagged Screenshot             |  Tagged Text Representation
:-------------------------:|:-------------------------:
![tagged](https://github.com/reworkd/tarsier/blob/main/.github/assets/tagged.png)  |  ![tagged](https://github.com/reworkd/tarsier/blob/main/.github/assets/tagged_text.png)


## Installation

```shell
pip install tarsier
```

## Usage

Visit our [cookbook](https://github.com/reworkd/Tarsier/tree/main/cookbook) for agent examples using Tarsier:

- [An autonomous LangChain web agent](https://github.com/reworkd/tarsier/blob/main/cookbook/langchain-web-agent.ipynb) 🦜⛓️
- [An autonomous LlamaIndex web agent](https://github.com/reworkd/tarsier/blob/main/cookbook/llama-index-web-agent.ipynb) 🦙

We currently support 2 OCR engines: Google Vision and Microsoft Azure.
To create service account credentials for Google, follow the instructions on this SO answer https://stackoverflow.com/a/46290808/1780891

The credentials for Microsoft Azure are stored as a simple JSON consisting of an API key and
an endpoint

```json
{
  "key": "<enter_your_api_key>",
  "endpoint": "<enter_your_api_endpoint>"
}
```
These values can be found in the keys and endpoint section of the computer vision resource. See the instructions at https://learn.microsoft.com/en-us/answers/questions/854952/dont-find-your-key-and-your-endpoint

Otherwise, basic Tarsier usage might look like the following:

```python
import asyncio

from playwright.async_api import async_playwright
from tarsier import Tarsier, GoogleVisionOCRService, MicrosoftAzureOCRService
import json

def load_ocr_credentials(json_file_path):
    with open(json_file_path) as f:
        credentials = json.load(f)
    return credentials

async def main():
    # To create the service account key, follow the instructions on this SO answer https://stackoverflow.com/a/46290808/1780891

    google_cloud_credentials = load_ocr_credentials('./google_service_acc_key.json')
    #microsoft_azure_credentials = load_ocr_credentials('./microsoft_azure_credentials.json')

    ocr_service = GoogleVisionOCRService(google_cloud_credentials)
    #ocr_service = MicrosoftAzureOCRService(microsoft_azure_credentials)

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
- [x] Improve OCR text performance
- [ ] Add options to customize tagging styling
- [ ] Add support for other browsers drivers as necessary

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
