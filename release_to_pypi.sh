#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${PYPI_TOKEN:-}" ]]; then
  echo "PYPI_TOKEN is not set."
  exit 1
fi

python -m pip install --upgrade pip build twine
rm -rf dist build ./*.egg-info
python -m build
twine check dist/*
twine upload --repository pypi dist/* -u __token__ -p "${PYPI_TOKEN}"
