"""Template-only tests: the template's own packaging and tailoring contract.

**Do not copy this file into a project derived from this template.** It checks
that the *template* generates and tailors correctly, which is not part of a
derived project's contract. `tailor_template_cleanup.sh` deletes it for that
reason.

These tests are deliberately cheap: they read configuration and run the
tailoring script against a throwaway copy. Nothing here rebuilds the project.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, cast

import pytest
import yaml

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover - only on the 3.10 leg of the CI matrix
    # tomllib entered the stdlib in 3.11; the package supports 3.10.
    import tomli as tomllib

REPO_ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = REPO_ROOT / "pyproject.toml"
TAILOR_SCRIPT = REPO_ROOT / "tailor_template_cleanup.sh"
TEMPLATE_NAME = "template_python_project"
TEMPLATE_WORKSPACE = "python_template_project.code-workspace"
ISSUE_TEMPLATE_DIR = REPO_ROOT / ".github" / "ISSUE_TEMPLATE"
PULL_REQUEST_TEMPLATE = REPO_ROOT / ".github" / "pull_request_template.md"


@pytest.fixture(scope="module")
def config() -> dict[str, Any]:
    """Parsed pyproject.toml."""
    with PYPROJECT.open("rb") as handle:
        return tomllib.load(handle)


class TestPackagingContract:
    """Invariants the template promises about its own packaging."""

    @pytest.mark.unit
    def test_uses_scikit_build_core_backend(self, config: dict[str, Any]) -> None:
        assert config["build-system"]["build-backend"] == "scikit_build_core.build"

    @pytest.mark.unit
    def test_build_requirements_present(self, config: dict[str, Any]) -> None:
        requires = " ".join(config["build-system"]["requires"])
        for package in ("scikit-build-core", "pybind11", "setuptools-scm"):
            assert package in requires, f"{package} missing from build-system.requires"

    @pytest.mark.unit
    def test_version_is_dynamic_from_vcs(self, config: dict[str, Any]) -> None:
        assert "version" in config["project"]["dynamic"]
        provider = config["tool"]["scikit-build"]["metadata"]["version"]["provider"]
        assert provider == "scikit_build_core.metadata.setuptools_scm"
        assert "setuptools_scm" in config["tool"]

    @pytest.mark.unit
    def test_no_setup_py(self) -> None:
        # The build is pyproject.toml-only by design.
        assert not (REPO_ROOT / "setup.py").exists()
        assert not (REPO_ROOT / "setup.cfg").exists()

    @pytest.mark.unit
    def test_dev_tooling_uses_dependency_groups(self, config: dict[str, Any]) -> None:
        # PEP 735: dev tooling belongs in [dependency-groups]; extras are for
        # genuine runtime needs of installed-package users.
        groups = config["dependency-groups"]
        for group in ("test", "lint", "docs", "ext", "dev"):
            assert group in groups, f"missing dependency group: {group}"

        extras = config["project"].get("optional-dependencies", {})
        for leaked in ("dev", "docs", "lint", "test"):
            assert leaked not in extras, f"dev tooling leaked into extras: {leaked}"

    @pytest.mark.unit
    def test_extra_names_are_pep685_normalized(self, config: dict[str, Any]) -> None:
        for name in config["project"].get("optional-dependencies", {}):
            assert name == name.lower(), f"extra '{name}' is not lowercase"
            assert "_" not in name, f"extra '{name}' must use hyphens, not underscores"

    @pytest.mark.unit
    def test_license_uses_pep639_expression(self, config: dict[str, Any]) -> None:
        assert isinstance(config["project"]["license"], str)
        assert config["project"]["license-files"]
        # The classifier form is deprecated once the SPDX expression is used.
        classifiers = config["project"].get("classifiers", [])
        assert not any(c.startswith("License ::") for c in classifiers)

    @pytest.mark.unit
    def test_pytest_does_not_put_src_on_pythonpath(self, config: dict[str, Any]) -> None:
        # A src entry would shadow the installed package with the source tree,
        # which never contains the compiled extension -- so every native test
        # would silently skip while the suite reported green.
        assert "pythonpath" not in config["tool"]["pytest"]["ini_options"]

    @pytest.mark.unit
    def test_mypy_does_not_pin_python_version(self, config: dict[str, Any]) -> None:
        # Pinning it makes mypy parse third-party stubs under those syntax
        # rules; modern numpy stubs need 3.12+ to parse at all.
        assert "python_version" not in config["tool"]["mypy"]

    @pytest.mark.unit
    def test_py_typed_marker_present(self) -> None:
        assert (REPO_ROOT / "src" / TEMPLATE_NAME / "py.typed").is_file()


class TestExtensionContract:
    """Invariants about the compiled half."""

    @pytest.mark.unit
    def test_cmake_entry_points_exist(self) -> None:
        for relative in (
            "CMakeLists.txt",
            "cmake/HandlePybind11.cmake",
            "cmake/HandleExternalLibs.cmake",
            "src/cpp/CMakeLists.txt",
            "src/cpp/bindings.cpp",
            "src/cpp/template_ext.hpp",
            "src/cpp/template_ext.cpp",
        ):
            assert (REPO_ROOT / relative).is_file(), f"missing {relative}"

    @pytest.mark.unit
    def test_logic_is_independent_of_pybind11(self) -> None:
        # template_ext.* must stay reusable from plain C++ and testable without
        # Python, so it may not include any pybind11 header. Comments may of
        # course mention pybind11, so check the #include lines specifically.
        for name in ("template_ext.hpp", "template_ext.cpp"):
            content = (REPO_ROOT / "src" / "cpp" / name).read_text()
            includes = [
                line for line in content.splitlines() if line.lstrip().startswith("#include")
            ]
            offending = [line for line in includes if "pybind11" in line or "Python.h" in line]
            assert not offending, f"{name} must not include pybind11/Python: {offending}"

    @pytest.mark.unit
    def test_extension_installs_into_the_package(self) -> None:
        root_cmake = (REPO_ROOT / "CMakeLists.txt").read_text()
        extension_cmake = (REPO_ROOT / "cmake" / "HandlePybind11.cmake").read_text()
        source_cmake = (REPO_ROOT / "src" / "cpp" / "CMakeLists.txt").read_text()

        # Distribution metadata cannot own the destination because a project
        # may deliberately use a different import package name.
        assert 'set(TPP_PYTHON_PACKAGE "template_python_project")' in root_cmake
        assert 'DESTINATION "${TPP_PYTHON_PACKAGE}"' in extension_cmake
        assert 'DESTINATION "${TPP_PYTHON_PACKAGE}"' in source_cmake
        assert "DESTINATION ${SKBUILD_PROJECT_NAME}" not in extension_cmake + source_cmake

    @pytest.mark.unit
    def test_version_uses_full_pep440_string(self) -> None:
        # SKBUILD_PROJECT_VERSION is truncated by CMake's project(VERSION) and
        # loses PEP 440 suffixes such as ".dev1".
        content = (REPO_ROOT / "CMakeLists.txt").read_text()
        assert "SKBUILD_PROJECT_VERSION_FULL" in content

    @pytest.mark.unit
    def test_all_external_lib_patterns_documented(self) -> None:
        content = (REPO_ROOT / "cmake" / "HandleExternalLibs.cmake").read_text()
        for pattern in ("find_package", "FetchContent", "add_subdirectory"):
            assert pattern in content, f"wiring pattern not documented: {pattern}"


class TestContributionTemplates:
    """Contribution forms must remain valid and specific to this repository."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("filename", "expected_label"),
        [("bug_report.yml", "bug"), ("feature_request.yml", "enhancement")],
    )
    def test_issue_forms_are_valid(self, filename: str, expected_label: str) -> None:
        form = _load_yaml(ISSUE_TEMPLATE_DIR / filename)

        assert form["labels"] == [expected_label]
        body = cast(list[dict[str, Any]], form["body"])
        ids = [str(item["id"]) for item in body]
        assert len(ids) == len(set(ids)), f"duplicate IDs in {filename}"

        dropdowns = [item for item in body if item.get("type") == "dropdown"]
        for dropdown in dropdowns:
            attributes = cast(dict[str, Any], dropdown["attributes"])
            options = cast(list[str], attributes["options"])
            assert options
            assert all(option.strip() for option in options)

    @pytest.mark.unit
    def test_contact_links_target_this_repository(self) -> None:
        config = _load_yaml(ISSUE_TEMPLATE_DIR / "config.yml")
        contacts = cast(list[dict[str, Any]], config["contact_links"])

        assert contacts
        for contact in contacts:
            assert str(contact["url"]).startswith(
                "https://github.com/PeterCalifano/python_template_project/"
            )

    @pytest.mark.unit
    def test_pull_request_template_stays_concise(self) -> None:
        content = PULL_REQUEST_TEMPLATE.read_text()

        for heading in (
            "## Summary",
            "## Main Changes",
            "## Testing / Validation",
            "## Notes For Reviewers",
        ):
            assert heading in content


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="the tailoring script requires a POSIX shell and utilities",
)
class TestTailoringScript:
    """The tailoring script must be safe by default and correct when applied."""

    @pytest.mark.unit
    def test_script_is_executable(self) -> None:
        assert TAILOR_SCRIPT.is_file()
        assert os.access(TAILOR_SCRIPT, os.X_OK), "tailor script is not executable"

    @pytest.mark.unit
    def test_script_has_valid_syntax(self) -> None:
        result = subprocess.run(
            ["bash", "-n", str(TAILOR_SCRIPT)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr

    @pytest.mark.integration
    def test_list_is_non_destructive(self, tmp_path: Path) -> None:
        work = _copy_template(tmp_path / "listing")
        before = _tree_snapshot(work)

        result = subprocess.run(
            [str(work / "tailor_template_cleanup.sh"), "--list", "--root", str(work)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert _tree_snapshot(work) == before, "--list modified the tree"

    @pytest.mark.integration
    def test_refuses_unrelated_directory(self, tmp_path: Path) -> None:
        # A mistyped --root must not delete someone's unrelated files.
        stranger = tmp_path / "not-the-template"
        stranger.mkdir()
        (stranger / "important.txt").write_text("do not delete me")

        result = subprocess.run(
            [str(TAILOR_SCRIPT), "--apply", "--yes", "--root", str(stranger)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode != 0
        assert (stranger / "important.txt").is_file()

    @pytest.mark.integration
    def test_rejects_invalid_package_name(self, tmp_path: Path) -> None:
        work = _copy_template(tmp_path / "badname")
        result = subprocess.run(
            [
                str(work / "tailor_template_cleanup.sh"),
                "--apply",
                "--yes",
                "--root",
                str(work),
                "--package-name",
                "not-a-valid-identifier",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode != 0
        assert "identifier" in (result.stderr + result.stdout)

    @pytest.mark.integration
    def test_warns_about_uppercase_package_name(self, tmp_path: Path) -> None:
        work = _copy_template(tmp_path / "uppercase")
        result = subprocess.run(
            [
                str(work / "tailor_template_cleanup.sh"),
                "--dry-run",
                "--root",
                str(work),
                "--package-name",
                "DemoPkg",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0, result.stderr
        assert "conventionally lowercase" in result.stderr

    @pytest.mark.integration
    def test_package_only_rename_preserves_distribution(self, tmp_path: Path) -> None:
        work = _copy_template(tmp_path / "package-only")
        result = subprocess.run(
            [
                str(work / "tailor_template_cleanup.sh"),
                "--apply",
                "--yes",
                "--root",
                str(work),
                "--package-name",
                "renamed_package",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0, result.stderr
        with (work / "pyproject.toml").open("rb") as handle:
            tailored = tomllib.load(handle)

        assert tailored["project"]["name"] == TEMPLATE_NAME
        assert tailored["tool"]["scikit-build"]["wheel"]["packages"] == ["src/renamed_package"]
        assert 'set(TPP_PYTHON_PACKAGE "renamed_package")' in (work / "CMakeLists.txt").read_text()

    @pytest.mark.integration
    def test_rename_leaves_no_template_references(self, tmp_path: Path) -> None:
        work = _copy_template(tmp_path / "renamed", initialize_git=True)

        result = subprocess.run(
            [
                str(work / "tailor_template_cleanup.sh"),
                "--apply",
                "--yes",
                "--root",
                str(work),
                "--project-name",
                "demo-dist",
                "--package-name",
                "demo_pkg",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr

        assert (work / "src" / "demo_pkg").is_dir()
        assert not (work / "src" / TEMPLATE_NAME).exists()

        leftovers = [
            path.relative_to(work)
            for path in _text_files(work)
            if TEMPLATE_NAME in path.read_text(errors="ignore")
        ]
        assert not leftovers, f"template name still referenced in: {leftovers}"

        with (work / "pyproject.toml").open("rb") as handle:
            tailored = tomllib.load(handle)
        assert tailored["project"]["name"] == "demo-dist"
        assert tailored["tool"]["scikit-build"]["wheel"]["packages"] == ["src/demo_pkg"]
        assert 'set(TPP_PYTHON_PACKAGE "demo_pkg")' in (work / "CMakeLists.txt").read_text()

        # Template-development files must be gone.
        for removed in (
            "CLAUDE.md",
            "CONTEXT.md",
            "TODO",
            "doc/developments",
            "tests/test_template_conformance.py",
        ):
            assert not (work / removed).exists(), f"{removed} survived tailoring"

        assert (work / "AGENTS.md").is_file()
        assert (work / "demo_pkg.code-workspace").is_file()
        assert not (work / TEMPLATE_WORKSPACE).exists()
        assert os.access(work / "tailor_template_cleanup.sh", os.X_OK)
        assert not list(work.rglob("*.tailor-template-backup"))

    @pytest.mark.integration
    def test_no_extension_produces_pure_python_project(self, tmp_path: Path) -> None:
        work = _copy_template(tmp_path / "pure", initialize_git=True)

        result = subprocess.run(
            [
                str(work / "tailor_template_cleanup.sh"),
                "--apply",
                "--yes",
                "--no-extension",
                "--root",
                str(work),
                "--project-name",
                "pure-pkg",
                "--package-name",
                "pure_pkg",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr

        for removed in (
            "src/cpp",
            "cmake",
            "CMakeLists.txt",
            "build_ext.sh",
            "src/pure_pkg/_core.pyi",
            "tests/test_extension.py",
            "CLAUDE.md",
        ):
            assert not (work / removed).exists(), f"{removed} survived --no-extension"

        assert (work / "pure_pkg.code-workspace").is_file()
        assert not (work / TEMPLATE_WORKSPACE).exists()

        with (work / "pyproject.toml").open("rb") as handle:
            tailored = tomllib.load(handle)
        assert tailored["tool"]["scikit-build"]["wheel"]["cmake"] is False

        # setuptools-scm creates this module during installation. Supply that
        # generated boundary so this source-level check isolates the tailored
        # pure-Python runtime without performing a nested package build.
        (work / "src" / "pure_pkg" / "_version.py").write_text('__version__ = "0.0.0"\n')

        # The package must still import and work without the extension.
        result = subprocess.run(
            [sys.executable, "-c", "import pure_pkg; print(pure_pkg.vector_norm([3.0, 4.0]))"],
            capture_output=True,
            text=True,
            cwd=work / "src",
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert "5.0" in result.stdout


# --- helpers ---------------------------------------------------------------


def _copy_template(destination: Path, *, initialize_git: bool = False) -> Path:
    """Copy the repository into a throwaway directory.

    Args:
        destination: Directory that will receive the template copy.
        initialize_git: Whether to commit the copied files in a temporary Git repository.

    Returns:
        The copied template root.
    """
    shutil.copytree(
        REPO_ROOT,
        destination,
        ignore=shutil.ignore_patterns(
            ".git",
            ".venv",
            "build",
            "dist",
            "_build",
            "_autosummary",
            "__pycache__",
            "*.egg-info",
            "*.so",
            ".mypy_cache",
            ".pytest_cache",
        ),
    )

    if initialize_git:
        subprocess.run(["git", "init", "--quiet"], cwd=destination, check=True)
        subprocess.run(["git", "add", "--all"], cwd=destination, check=True)
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=Template Test",
                "-c",
                "user.email=template-test@example.invalid",
                "commit",
                "--quiet",
                "-m",
                "Initialize fixture",
            ],
            cwd=destination,
            check=True,
        )

    return destination


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML mapping used by a GitHub contribution form."""
    return cast(dict[str, Any], yaml.safe_load(path.read_text()))


_TEXT_SUFFIXES = {
    ".toml",
    ".py",
    ".pyi",
    ".md",
    ".rst",
    ".txt",
    ".cfg",
    ".yml",
    ".yaml",
    ".sh",
    ".json",
    ".cmake",
    ".cpp",
    ".hpp",
    ".h",
    ".in",
    ".code-workspace",
}


def _text_files(root: Path) -> list[Path]:
    """Every text file under root that the tailoring script would rewrite."""
    skip = {".git", ".venv", "build", "dist", "__pycache__", "_build", "_autosummary"}
    return [
        path
        for path in root.rglob("*")
        if path.is_file()
        and not skip.intersection(path.parts)
        and (path.suffix in _TEXT_SUFFIXES or path.name.startswith("Dockerfile"))
    ]


def _tree_snapshot(root: Path) -> set[tuple[str, int]]:
    """Relative paths and sizes, for detecting any modification."""
    return {
        (str(path.relative_to(root)), path.stat().st_size)
        for path in root.rglob("*")
        if path.is_file() and ".git" not in path.parts
    }
