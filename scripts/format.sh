#!/bin/sh
cd "$(dirname "$0")" || exit 1
cd .. || exit 1

printf "Formatting Code 🧹"
poetry run black .

printf "\nSorting imports 🧹\n"
poetry run isort .