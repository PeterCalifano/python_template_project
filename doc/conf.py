"""Sphinx configuration for the template documentation."""

from __future__ import annotations

import sys
from importlib import import_module
from pathlib import Path

# Make the src-layout package importable without installing it, so `make html`
# works in a fresh checkout.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

project = "template_python_project"
author = "Pietro Califano"
copyright = "2026, Pietro Califano"

try:
    version = import_module("template_python_project").__version__
except ImportError:
    version = "0.0.0"

release = version

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.githubpages",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx_rtd_theme",
    "myst_parser",
]

# Documentation must build on a machine with no compiler, so the compiled
# extension is mocked rather than imported. Without this, autodoc would fail on
# any docs build that did not first compile the C++ -- which is exactly the
# situation on a docs-only CI runner.
autodoc_mock_imports = ["template_python_project._core"]

# Lets doc/*.md files be written in Markdown alongside the .rst files.
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

templates_path = ["_templates"]
exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
    # Staged development plans are working documents, not published docs.
    "developments/*",
]

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

autosummary_generate = True
napoleon_google_docstring = True
napoleon_numpy_docstring = True
autodoc_member_order = "bysource"
autodoc_typehints = "description"

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
}


def setup(app: object) -> None:
    """Register the theme override stylesheet.

    Args:
        app: The Sphinx application instance.
    """
    app.add_css_file("theme_overrides.css")  # type: ignore[attr-defined]
