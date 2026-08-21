#!/usr/bin/env bash
# Turn this template into a real project: rename the distribution and import
# package everywhere, and remove the files that only matter while developing
# the template itself.

set -Eeuo pipefail
IFS=$'\n\t'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="${SCRIPT_DIR}"

TEMPLATE_DIST_NAME="template_python_project"
TEMPLATE_PKG_NAME="template_python_project"
TEMPLATE_WORKSPACE_NAME="python_template_project.code-workspace"

APPLY=0
LIST_ONLY=0
DRY_RUN=0
ASSUME_YES=0
NO_EXTENSION=0
KEEP_EXAMPLES=0
NEW_DIST_NAME=""
NEW_PKG_NAME=""
TARGET_DIST_NAME=""

info() { printf '\033[34m[INFO]\033[0m %s\n' "$*"; }
warn() { printf '\033[33m[WARN]\033[0m %s\n' "$*" >&2; }
die() { printf '\033[31m[ERROR]\033[0m %s\n' "$*" >&2; exit 1; }
action() { printf '\033[32m[DO]\033[0m %s\n' "$*"; }

# Use one in-place editing path that works with GNU sed and BSD sed. The
# explicit backup also preserves the original file mode.
sed_in_place() {
    local expression_="$1" file_="$2"
    local backup_suffix_=".tailor-template-backup"
    local backup_path_="${file_}${backup_suffix_}"

    [[ ! -e "${backup_path_}" ]] \
        || die "Refusing to overwrite existing backup: ${backup_path_}"
    sed -i"${backup_suffix_}" -e "${expression_}" "${file_}"
    rm -f -- "${backup_path_}"
}

usage() {
    cat <<'EOF'
Usage:
  ./tailor_template_cleanup.sh --list
  ./tailor_template_cleanup.sh --apply --project-name <dist> --package-name <import> [options]

Purpose:
  Rename the distribution and import package, then delete the files that exist
  only to develop this template.

Options:
  --list                     Print what would be removed and renamed, then exit.
  --apply                    Perform the changes.
  --dry-run                  Print every change without writing anything.
  --yes                      Do not prompt for confirmation.
  --project-name <name>      New distribution name, e.g. my-cool-lib
                             (hyphens allowed; used by `pip install <name>`).
  --package-name <name>      New import package name, e.g. my_cool_lib
                             (a valid Python identifier; used by `import <name>`).
  --no-extension             Remove the pybind11/CMake stack for a pure-Python
                             project, and set wheel.cmake = false.
  --keep-examples            Keep examples/ (removed by default).
  --root <dir>               Operate on this directory instead of the script's.
  -h, --help                 Show this help.

Examples:
  ./tailor_template_cleanup.sh --list
  ./tailor_template_cleanup.sh --apply --project-name my-lib --package-name my_lib --yes
  ./tailor_template_cleanup.sh --apply --no-extension --project-name my-lib \
      --package-name my_lib --yes
EOF
}

# Files and directories that exist only to develop the template itself.
#
# AGENTS.md is generic guidance for projects created from this template.
# CLAUDE.md documents this template's maintenance workflow and is removed.
template_development_paths=(
    "CLAUDE.md"
    "CONTEXT.md"
    "TODO"
    "doc/developments"
    "tests/test_template_conformance.py"
)

# Removed by --no-extension.
extension_paths=(
    "src/cpp"
    "cmake"
    "CMakeLists.txt"
    "build_ext.sh"
)

while [[ $# -gt 0 ]]; do
    case "$1" in
        --list) LIST_ONLY=1; shift ;;
        --apply) APPLY=1; shift ;;
        --dry-run) DRY_RUN=1; shift ;;
        --yes) ASSUME_YES=1; shift ;;
        --no-extension) NO_EXTENSION=1; shift ;;
        --keep-examples) KEEP_EXAMPLES=1; shift ;;
        --project-name) [[ $# -ge 2 ]] || die "--project-name requires a value"; NEW_DIST_NAME="$2"; shift 2 ;;
        --package-name) [[ $# -ge 2 ]] || die "--package-name requires a value"; NEW_PKG_NAME="$2"; shift 2 ;;
        --root) [[ $# -ge 2 ]] || die "--root requires a directory"; ROOT_DIR="$2"; shift 2 ;;
        -h|--help) usage; exit 0 ;;
        *) die "Unknown option: $1 (try --help)" ;;
    esac
done

[[ -d "${ROOT_DIR}" ]] || die "Root directory does not exist: ${ROOT_DIR}"
ROOT_DIR="$(cd "${ROOT_DIR}" && pwd)"

# Refuse to operate on a directory that is not this template. Without this a
# mistyped --root could delete unrelated files.
[[ -f "${ROOT_DIR}/pyproject.toml" ]] \
    || die "No pyproject.toml in ${ROOT_DIR}; refusing to operate on it."
grep -q "${TEMPLATE_PKG_NAME}" "${ROOT_DIR}/pyproject.toml" \
    || die "${ROOT_DIR}/pyproject.toml does not reference ${TEMPLATE_PKG_NAME}; already tailored?"

validate_package_name() {
    local name_="$1" lowercase_name_
    [[ "${name_}" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] \
        || die "Import package name must be a valid Python identifier: '${name_}'"
    # PEP 8 discourages capitals, and a hyphen is outright invalid.
    lowercase_name_="$(printf '%s' "${name_}" | LC_ALL=C tr '[:upper:]' '[:lower:]')"
    [[ "${name_}" == "${lowercase_name_}" ]] \
        || warn "Import package names are conventionally lowercase: '${name_}'"
}

validate_dist_name() {
    local name_="$1"
    # PEP 508 name grammar.
    [[ "${name_}" =~ ^([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9._-]*[A-Za-z0-9])$ ]] \
        || die "Distribution name is not PEP 508 valid: '${name_}'"
}

print_plan() {
    info "Root: ${ROOT_DIR}"
    echo
    echo "Template-development files to remove:"
    local path_
    for path_ in "${template_development_paths[@]}"; do
        if [[ -e "${ROOT_DIR}/${path_}" ]]; then
            echo "  - ${path_}"
        fi
    done
    if [[ ${KEEP_EXAMPLES} -eq 0 && -d "${ROOT_DIR}/examples" ]]; then
        echo "  - examples/            (keep with --keep-examples)"
    fi
    echo
    echo "Retained (inherited by the derived project):"
    echo "  = AGENTS.md            generic agent development guidance"
    if [[ ${NO_EXTENSION} -eq 1 ]]; then
        echo
        echo "Extension files to remove (--no-extension):"
        for path_ in "${extension_paths[@]}"; do
            [[ -e "${ROOT_DIR}/${path_}" ]] && echo "  - ${path_}"
        done
        echo "  and: set wheel.cmake = false in pyproject.toml"
    fi
    echo
    echo "Renaming:"
    if [[ -n "${NEW_DIST_NAME}" ]]; then
        echo "  distribution : ${TEMPLATE_DIST_NAME} -> ${NEW_DIST_NAME}"
    else
        echo "  distribution : (unchanged; pass --project-name to rename)"
    fi
    if [[ -n "${NEW_PKG_NAME}" ]]; then
        echo "  import pkg   : ${TEMPLATE_PKG_NAME} -> ${NEW_PKG_NAME}"
        echo "  directory    : src/${TEMPLATE_PKG_NAME}/ -> src/${NEW_PKG_NAME}/"
        echo "  workspace    : ${TEMPLATE_WORKSPACE_NAME} -> ${NEW_PKG_NAME}.code-workspace"
    else
        echo "  import pkg   : (unchanged; pass --package-name to rename)"
    fi
}

if [[ ${LIST_ONLY} -eq 1 ]]; then
    print_plan
    exit 0
fi

if [[ ${APPLY} -eq 0 && ${DRY_RUN} -eq 0 ]]; then
    usage
    die "Nothing to do: pass --list, --dry-run, or --apply."
fi

if [[ -z "${NEW_PKG_NAME}" && -z "${NEW_DIST_NAME}" && ${NO_EXTENSION} -eq 0 ]]; then
    warn "No --project-name or --package-name given: only template files will be removed."
fi

[[ -n "${NEW_PKG_NAME}" ]] && validate_package_name "${NEW_PKG_NAME}"
[[ -n "${NEW_DIST_NAME}" ]] && validate_dist_name "${NEW_DIST_NAME}"

# A rename that only sets one of the two names is usually a mistake.
if [[ -n "${NEW_DIST_NAME}" && -z "${NEW_PKG_NAME}" ]]; then
    warn "--project-name given without --package-name; the import name stays ${TEMPLATE_PKG_NAME}."
fi

print_plan
echo

if [[ ${DRY_RUN} -eq 1 ]]; then
    info "Dry run: no changes written."
fi

if [[ ${APPLY} -eq 1 && ${ASSUME_YES} -eq 0 ]]; then
    read -r -p "Proceed? [y/N] " reply_
    [[ "${reply_}" =~ ^[Yy]$ ]] || die "Aborted."
fi

run() {
    if [[ ${DRY_RUN} -eq 1 ]]; then
        action "(dry-run) $*"
    else
        action "$*"
        "$@"
    fi
}

# --- 1. Remove template-development files ---------------------------------

remove_paths() {
    local path_ target_
    for path_ in "$@"; do
        target_="${ROOT_DIR}/${path_}"
        [[ -e "${target_}" ]] || continue
        run rm -rf -- "${target_}"
    done
}

remove_paths "${template_development_paths[@]}"

if [[ ${KEEP_EXAMPLES} -eq 0 ]]; then
    remove_paths "examples"
fi

if [[ ${NO_EXTENSION} -eq 1 ]]; then
    remove_paths "${extension_paths[@]}"
    remove_paths "src/${TEMPLATE_PKG_NAME}/_core.pyi"
    remove_paths "tests/test_extension.py"
fi

# --- 2. Rename the import package directory --------------------------------

if [[ -n "${NEW_PKG_NAME}" && "${NEW_PKG_NAME}" != "${TEMPLATE_PKG_NAME}" ]]; then
    if [[ -d "${ROOT_DIR}/src/${TEMPLATE_PKG_NAME}" ]]; then
        [[ -e "${ROOT_DIR}/src/${NEW_PKG_NAME}" ]] \
            && die "src/${NEW_PKG_NAME} already exists; refusing to overwrite."
        # A filesystem rename also works when files were removed first; Git
        # detects the rename from the resulting content.
        run mv "${ROOT_DIR}/src/${TEMPLATE_PKG_NAME}" "${ROOT_DIR}/src/${NEW_PKG_NAME}"
    fi
fi

# --- 3. Rewrite references throughout the tree -----------------------------

# Text files that may mention either name. Binary files, build output, the
# virtualenv, and .git are all excluded.
collect_text_files() {
    find "${ROOT_DIR}" \
        \( -path "${ROOT_DIR}/.git" \
        -o -path "${ROOT_DIR}/.venv" \
        -o -path "${ROOT_DIR}/build" \
        -o -path "${ROOT_DIR}/dist" \
        -o -path "${ROOT_DIR}/doc/_build" \
        -o -path "${ROOT_DIR}/doc/_autosummary" \
        -o -name "__pycache__" \
        -o -name "*.egg-info" \) -prune -o \
        -type f \( -name "*.toml" -o -name "*.py" -o -name "*.pyi" \
        -o -name "*.md" -o -name "*.rst" -o -name "*.txt" -o -name "*.cfg" \
        -o -name "*.yml" -o -name "*.yaml" -o -name "*.sh" -o -name "*.json" \
        -o -name "*.cmake" -o -name "CMakeLists.txt" -o -name "*.cpp" \
        -o -name "*.hpp" -o -name "*.h" -o -name "*.in" \
        -o -name "Dockerfile*" -o -name "*.code-workspace" \) -print
}

replace_in_files() {
    local from_="$1" to_="$2"
    [[ -n "${from_}" && -n "${to_}" && "${from_}" != "${to_}" ]] || return 0

    local file_ changed_=0
    while IFS= read -r file_; do
        grep -q -- "${from_}" "${file_}" 2>/dev/null || continue
        changed_=$((changed_ + 1))
        if [[ ${DRY_RUN} -eq 1 ]]; then
            action "(dry-run) rewrite ${from_} -> ${to_} in ${file_#"${ROOT_DIR}"/}"
        else
            # Escape the replacement for sed: & and \ are special.
            local escaped_to_
            escaped_to_="$(printf '%s' "${to_}" | sed -e 's/[\\&|]/\\&/g')"
            sed_in_place "s|${from_}|${escaped_to_}|g" "${file_}"
        fi
    done < <(collect_text_files)

    info "Rewrote '${from_}' -> '${to_}' in ${changed_} file(s)."
}

# Order matters: the import package name is a substring of nothing else here,
# but rewriting the distribution name first would be wrong if the two differ
# only by separator. Replace the longer/more specific pattern first.
if [[ -n "${NEW_PKG_NAME}" ]]; then
    replace_in_files "${TEMPLATE_PKG_NAME}" "${NEW_PKG_NAME}"
fi

# Package replacement may also rewrite [project].name when the template starts
# with matching distribution and import names. Set the requested distribution
# explicitly, or restore the original when only the import package changes.
if [[ -n "${NEW_DIST_NAME}" || -n "${NEW_PKG_NAME}" ]]; then
    TARGET_DIST_NAME="${NEW_DIST_NAME:-${TEMPLATE_DIST_NAME}}"
    if [[ ${DRY_RUN} -eq 1 ]]; then
        action "(dry-run) set [project].name = ${TARGET_DIST_NAME} in pyproject.toml"
    else
        # Only the [project] name field, not every occurrence.
        sed_in_place \
            "1,/^name = .*/s|^name = .*|name = \"${TARGET_DIST_NAME}\"|" \
            "${ROOT_DIR}/pyproject.toml"
        action "set [project].name = ${TARGET_DIST_NAME}"
    fi
fi

# --- 4. Pure-Python mode ---------------------------------------------------

if [[ ${NO_EXTENSION} -eq 1 ]]; then
    if [[ ${DRY_RUN} -eq 1 ]]; then
        action "(dry-run) set wheel.cmake = false in pyproject.toml"
    else
        sed_in_place \
            's|^wheel\.cmake = true|wheel.cmake = false|' \
            "${ROOT_DIR}/pyproject.toml"
        action "set wheel.cmake = false"
        warn "You may now also remove 'pybind11' from [build-system].requires."
        warn "src/*/_accel.py still has its pure-Python fallbacks and works as-is."
    fi
fi

# --- 5. Rename the VS Code workspace file ----------------------------------

if [[ -n "${NEW_PKG_NAME}" ]]; then
    old_workspace_="${ROOT_DIR}/${TEMPLATE_WORKSPACE_NAME}"
    if [[ -f "${old_workspace_}" ]]; then
        run mv "${old_workspace_}" "${ROOT_DIR}/${NEW_PKG_NAME}.code-workspace"
    fi
fi

echo
if [[ ${DRY_RUN} -eq 1 ]]; then
    info "Dry run complete. Nothing was changed."
else
    info "Tailoring complete."
    cat <<EOF

Next steps:
  python -m pip install --upgrade pip
  python -m pip install --group dev -e .
  pytest

Then review the diff before committing:
  git status
  git diff
EOF
fi
