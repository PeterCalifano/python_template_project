#!/usr/bin/env bash
set -euo pipefail

env_name="template-python-project"
python_version="3.11"
create_env=0
editable_mode=0
install_docs=0

usage() {
  cat <<'EOF'
Usage: ./conda_install.sh [options]

Options:
  -c, --create-env       Create the conda environment before installing
  -e, --editable         Install the package in editable mode
  -d, --docs             Install docs dependencies in addition to dev tools
  -n, --name NAME        Conda environment name (default: template-python-project)
  -p, --python VERSION   Python version for newly created envs (default: 3.11)
  -h, --help             Show this help text
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -c|--create-env)
      create_env=1
      shift
      ;;
    -e|--editable)
      editable_mode=1
      shift
      ;;
    -d|--docs)
      install_docs=1
      shift
      ;;
    -n|--name)
      env_name="$2"
      shift 2
      ;;
    -p|--python)
      python_version="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      usage
      exit 1
      ;;
  esac
done

if ! command -v conda >/dev/null 2>&1; then
  echo "conda is not available on PATH."
  exit 1
fi

source "$(conda info --base)/etc/profile.d/conda.sh"

if [[ $create_env -eq 1 ]]; then
  conda create -y -n "$env_name" "python=${python_version}"
fi

conda activate "$env_name"
python -m pip install --upgrade pip

install_args=(--group dev)
if [[ $install_docs -eq 1 ]]; then
  install_args+=(--group docs)
fi

if [[ $editable_mode -eq 1 ]]; then
  install_args+=(-e)
fi
install_args+=(.)

python -m pip install "${install_args[@]}"

echo "Installed template_python_project into conda env '${env_name}'."
echo "Optional GPU or Jetson-specific setup should be added in project-specific scripts under examples/."
