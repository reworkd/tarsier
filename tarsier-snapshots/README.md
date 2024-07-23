# About

This package is aimed at taking snapshots of pages to ensure Tarsier outputs are consistent and performant over time.

## How does it work?

We use MHTML pages found in our bananalyzer repo as site targets.
For each site on bananalyzer, we store both the screenshot of the page along with the OCR text output.
These sites will not change overtime therefore they serve as ideal candidates for snapshotting.

## How to use

- Create `.env` and add your credentials
- Run `poetry install`
- Run `poetry run python  tarsier_snapshots/snapshots.py`
