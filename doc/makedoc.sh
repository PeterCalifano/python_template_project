#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_dir="$(cd -- "${script_dir}/.." && pwd)"

while getopts "a:o:p:" opt; do
  case "$opt" in
    a) AUTOBUILD=1 ;;
    o) OUTPUT="${OPTARG:-doc/_build/html}" ;;
    p) PORT="${OPTARG:-8000}" ;;
    *) echo "Invalid option"; exit 1 ;;
  esac
done

AUTOBUILD=${AUTOBUILD:-0}
OUTPUT=${OUTPUT:-doc/_build/html}
PORT=${PORT:-8000}

cd "${repo_dir}"

if [[ "${AUTOBUILD}" -eq 1 ]]; then
  sphinx-autobuild doc "${OUTPUT}" --port "${PORT}"
else
  sphinx-build -b html doc "${OUTPUT}"
fi
