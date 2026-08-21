# Root CMake entry point for the compiled part of this Python package.
#
# This file is driven by scikit-build-core from inside PEP 517: `pip install .`
# configures and builds it automatically. It is not meant to be the primary
# entry point for humans -- use `./build_ext.sh` for a local development loop.
#
# For a pure-Python derived project, set `wheel.cmake = false` in
# pyproject.toml; this file is then never invoked and may be deleted.

cmake_minimum_required(VERSION 3.20...3.31)

# SKBUILD_PROJECT_NAME and SKBUILD_PROJECT_VERSION are injected by
# scikit-build-core from [project] in pyproject.toml, where the version itself
# comes from git tags via setuptools-scm. Declaring the project this way means
# the C++ side and the Python side can never report different versions.
#
# Fallbacks let a developer configure this tree directly with plain CMake
# (useful for IDE integration and compile_commands.json generation).
if(NOT DEFINED SKBUILD_PROJECT_NAME)
    set(SKBUILD_PROJECT_NAME "template_python_project")
endif()
if(NOT DEFINED SKBUILD_PROJECT_VERSION)
    set(SKBUILD_PROJECT_VERSION "0.0.0")
endif()

# The distribution name and Python import package may differ. The tailoring
# script rewrites this literal to the requested import name, while
# SKBUILD_PROJECT_NAME continues to own distribution metadata.
set(TPP_PYTHON_PACKAGE "template_python_project")

project(
    ${SKBUILD_PROJECT_NAME}
    VERSION ${SKBUILD_PROJECT_VERSION}
    DESCRIPTION "Compiled extension for ${SKBUILD_PROJECT_NAME}"
    LANGUAGES CXX)

list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake")

# CMake's project(VERSION) accepts only numeric MAJOR.MINOR.PATCH, so a PEP 440
# development version such as "0.3.0.dev1" is silently truncated to "0.3.0".
# scikit-build-core also exports the exact string; use that for anything the
# extension reports back to Python, so the two halves cannot disagree.
if(DEFINED SKBUILD_PROJECT_VERSION_FULL)
    set(TPP_VERSION_FULL "${SKBUILD_PROJECT_VERSION_FULL}")
else()
    set(TPP_VERSION_FULL "${PROJECT_VERSION}")
endif()

# --- Options ---------------------------------------------------------------

option(TPP_BUILD_EXTENSION "Build the pybind11 extension module" ON)
option(TPP_ENABLE_LTO "Enable link-time optimization for the extension" OFF)
option(TPP_WARNINGS_AS_ERRORS "Treat compiler warnings as errors" OFF)

# --- Global settings -------------------------------------------------------

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Extension modules are shared objects, so every object they contain must be
# position independent. Forgetting this is the single most common cause of
# "relocation R_X86_64_PC32 against symbol" link failures when a static
# third-party library gets pulled into the module.
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# Hide symbols by default. pybind11 exports what it needs explicitly; hiding
# the rest shrinks the module and avoids symbol clashes between two extensions
# that happen to vendor the same static library.
set(CMAKE_CXX_VISIBILITY_PRESET hidden)
set(CMAKE_VISIBILITY_INLINES_HIDDEN ON)

# Always emit a compilation database for clangd / VS Code C++ tooling.
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type" FORCE)
endif()

message(STATUS "${PROJECT_NAME} version ${PROJECT_VERSION} (${CMAKE_BUILD_TYPE})")

if(NOT TPP_BUILD_EXTENSION)
    message(STATUS "TPP_BUILD_EXTENSION=OFF -- no native module will be built.")
    return()
endif()

include(HandlePybind11)
include(HandleExternalLibs)

add_subdirectory(src/cpp)
