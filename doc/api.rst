API reference
=============

Public API
----------

.. autosummary::
   :toctree: _autosummary
   :recursive:

   template_python_project

Optional acceleration
---------------------

Every function below dispatches to the compiled ``_core`` extension when it is
available, and to an equivalent pure-Python implementation when it is not. Both
paths produce the same results and raise the same exceptions with the same
messages.

.. autodata:: template_python_project.HAS_EXTENSION
   :annotation: : bool

.. autofunction:: template_python_project.backend_name

.. autofunction:: template_python_project.vector_norm

.. autofunction:: template_python_project.scale_in_place

.. note::

   The compiled module ``template_python_project._core`` is mocked when these
   docs are built, so that documentation can be produced on a machine with no
   compiler. Its Python-visible signatures are described by the checked-in
   stub ``src/template_python_project/_core.pyi``.
