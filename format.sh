#!/bin/bash
cd "$(dirname "$0")" || exit 1

println() {
    printf "\n%s\n" "$1"
}

println "Formatting Tarsier 🍰"
poetry run ruff format .

println "Linting Tarsier 👀"
poetry run ruff check . --fix
poetry run mypy . || exit 1

println "Testing Tarsier 🧪"
poetry run pytest -q -vvv --ff . || exit 1
