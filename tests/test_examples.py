"""Smoke tests that keep the examples from rotting.

Examples are documentation that can be executed, which only stays true if
something executes them. These run each script in a subprocess and assert it
exits cleanly and prints what the docs say it prints.

The heavier external-C-library example (04) is not built here -- it has its own
build script and is covered by the docs -- but its sources are checked for the
two traps that make it silently wrong.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

import template_python_project as tpp

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"


def _run_example(name: str) -> subprocess.CompletedProcess[str]:
    """Execute an example script and return the completed process."""
    script = EXAMPLES_DIR / name
    assert script.is_file(), f"missing example: {script}"
    return subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


def _subprocess_backend() -> tuple[str, bool]:
    """Return (backend_name, has_extension) as a *subprocess* sees them.

    A fresh interpreter can resolve a different copy of the package than the
    one pytest imported -- for instance when a stray path entry shadows the
    installed package with the source tree, which never contains the compiled
    module. Asking the subprocess directly keeps these tests honest either way.
    """
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import template_python_project as t;"
            "print(t.backend_name());print(int(t.HAS_EXTENSION))",
        ],
        capture_output=True,
        text=True,
        timeout=120,
        check=True,
    )
    backend, has_extension = result.stdout.split()
    return backend, bool(int(has_extension))


@pytest.mark.integration
def test_pure_python_example_runs() -> None:
    result = _run_example("01_pure_python_usage.py")
    assert result.returncode == 0, result.stderr
    assert "hello from template_python_project" in result.stdout
    assert tpp.__version__ in result.stdout


@pytest.mark.integration
def test_extension_example_runs() -> None:
    _, subprocess_has_extension = _subprocess_backend()
    result = _run_example("02_pybind11_extension_usage.py")

    if not subprocess_has_extension:
        # Documented behaviour: exit 1 with actionable guidance, not a crash.
        assert result.returncode == 1
        assert "build_ext.sh" in result.stdout
        return

    assert result.returncode == 0, result.stderr
    # The zero-copy claim is the example's headline; assert it is demonstrated.
    assert "buffer moved  : False" in result.stdout
    assert "agree               : True" in result.stdout


@pytest.mark.integration
def test_fallback_example_runs() -> None:
    subprocess_backend, _ = _subprocess_backend()
    result = _run_example("03_accelerated_fallback.py")
    assert result.returncode == 0, result.stderr
    assert f"backend_name(): {subprocess_backend}" in result.stdout


class TestExternalLibraryExampleSources:
    """Static checks on example 04, which is not built during the test run.

    Both assertions below encode a bug that actually occurred while writing
    this template. Keeping them as tests means a well-meaning edit cannot
    quietly reintroduce either one.
    """

    EXAMPLE_DIR = EXAMPLES_DIR / "04_wire_external_c_library"

    @pytest.mark.unit
    def test_expected_files_exist(self) -> None:
        for relative in (
            "CMakeLists.txt",
            "README.md" if (self.EXAMPLE_DIR / "README.md").exists() else "demo.py",
            "demo.py",
            "bindings_mylib.cpp",
            "build_and_run.sh",
            "mylib/mylib.c",
            "mylib/mylib.h",
            "mylib/CMakeLists.txt",
        ):
            assert (self.EXAMPLE_DIR / relative).is_file(), f"missing {relative}"

    @pytest.mark.unit
    def test_static_library_is_position_independent(self) -> None:
        # A static library linked into a shared extension module must be PIC,
        # or linking fails with a relocation error.
        content = (self.EXAMPLE_DIR / "mylib" / "CMakeLists.txt").read_text()
        assert "POSITION_INDEPENDENT_CODE ON" in content

    @pytest.mark.unit
    def test_output_array_uses_explicit_shape_container(self) -> None:
        # py::array_t<double>(count) yields a zero-stride array in pybind11 3.x:
        # the shape looks right but every element reads back as element 0.
        content = (self.EXAMPLE_DIR / "bindings_mylib.cpp").read_text()
        assert "ShapeContainer" in content, (
            "output array must be constructed with an explicit shape container"
        )

    @pytest.mark.unit
    def test_c_header_has_extern_c_guard(self) -> None:
        # Without this a C++ compiler mangles the names and linking fails.
        content = (self.EXAMPLE_DIR / "mylib" / "mylib.h").read_text()
        assert 'extern "C"' in content
