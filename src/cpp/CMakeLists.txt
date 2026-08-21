# Build the pybind11 extension module.
#
# Adding a source file: append it to the SOURCES list below.
# Adding an external library: turn on the relevant option in
# cmake/HandleExternalLibs.cmake -- it registers itself into
# TPP_EXTERNAL_LINK_TARGETS and is picked up here with no edit to this file.

tpp_add_extension(_core
    SOURCES
        bindings.cpp
        template_ext.cpp
    LINK
        ${TPP_EXTERNAL_LINK_TARGETS}
)

# Keep the hand-maintained type stub next to the compiled module so that mypy
# and IDEs can see the extension's API. Regenerate it after changing the
# bindings with:
#
#   pybind11-stubgen template_python_project._core -o src/
#
set(_core_stub "${CMAKE_CURRENT_SOURCE_DIR}/../template_python_project/_core.pyi")
if(EXISTS "${_core_stub}")
    install(FILES "${_core_stub}" DESTINATION "${TPP_PYTHON_PACKAGE}")
endif()
