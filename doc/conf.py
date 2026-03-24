from __future__ import annotations

import os
import sys
from importlib import import_module

sys.path.insert(0, os.path.abspath("../src"))

project = "template_python_project"
author = "Pietro Califano"
copyright = "2026, Pietro Califano"

try:
    version = import_module("template_python_project").__version__
except Exception:
    version = "0.1.0"

release = version

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.githubpages",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx_rtd_theme",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

autosummary_generate = True
napoleon_google_docstring = True
napoleon_numpy_docstring = True
autodoc_member_order = "bysource"


def setup(app) -> None:
    app.add_css_file("theme_overrides.css")
