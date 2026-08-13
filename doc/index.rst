template_python_project documentation
=====================================

Reusable Python package template with a ``src`` layout, an optional pybind11
extension for wiring external C/C++ libraries, modern PEP-compliant packaging
via `scikit-build-core <https://scikit-build-core.readthedocs.io/>`_, tests,
docs, containers, and CI.

``pip install .`` compiles the extension -- there is no separate build step --
and one setting turns the same template into a pure-Python package.

.. toctree::
   :maxdepth: 2
   :caption: Guides

   template_usage
   extensions

.. toctree::
   :maxdepth: 2
   :caption: Reference

   api

Getting started
---------------

.. code-block:: bash

   python -m pip install --upgrade pip      # pip >= 25.1 for --group
   python -m pip install --group dev -e .
   pytest

Check which backend is active:

.. code-block:: bash

   python -c "import template_python_project as t; print(t.__version__, t.backend_name())"

The package imports and works whether or not the compiled extension was built.
:py:data:`template_python_project.HAS_EXTENSION` reports which path is in use,
and every native function has a pure-Python fallback with matching behaviour.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
