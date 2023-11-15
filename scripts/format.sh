#!/bin/sh
cd "$(dirname "$0")" || exit 1

printf "Formatting JS 🧹\n"
npm run format

printf "\nFormatting Python 🧹\n"
poetry run black .

printf "\nSorting imports 🧹\n"
poetry run isort .

printf "\nChecking types 🧹\n"
poetry run mypy .
