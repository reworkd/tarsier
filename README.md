<p align="center">
  <img src="./.github/assets/tarsier.png" height="300" alt="Tarsier Monkey" />
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
Tried using GPT-4(V) to automate web interactions? You've probably run into issues like these:
- How do you map from an LLM's responses back to web elements?
- How do you feed a "screenshot" to a text-only LLM?
- How do you screen capture an entire page?

At Reworkd, we found ourselves reusing the same utils to solve these problems across multiple projects, so we're now open-sourcing a simple little utils library for multimodal web agents... Tarsier!

Tarsier visually tags elements on a page, allowing GPT-4V to specify by tag which element to click. Tarsier also provides OCR utils to convert a page screenshot into a whitespace-structured string that an LLM without vision can understand.

## Usage
An agent using Tarsier might look like this:
```
# TODO
```

## Installation

`pip install tarsier`

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
