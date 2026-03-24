#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

python -m pip install --upgrade pip
python -m pip install -r "${script_dir}/requirements.txt"
