#!/bin/sh
cd "$(dirname "$0")" || exit 1

npm install
npm run build

poetry install