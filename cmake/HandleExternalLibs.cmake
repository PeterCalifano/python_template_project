# How to wire an external C or C++ library into the pybind11 extension.
#
# This module is the documented seam for the whole point of this template:
# taking a library that already exists and exposing it to Python. It defines
# three patterns, all inert by default, so the template builds with zero
# external dependencies until you turn one on.
#
# Pick the pattern by how the library reaches your machine:
#
#   Pattern 1  find_package()      the library is already installed
#                                  (apt, brew, conda, vcpkg, a system SDK)
#   Pattern 2  FetchContent        the library is source on the internet and
#                                  you want a pinned copy built with your flags
#   Pattern 3  add_subdirectory()  the source lives in this repo, usually as a
#                                  git submodule under lib/
#
# Whichever you pick, the result is the same: a CMake target name you pass to
# `tpp_add_extension(... LINK <target>)` in src/cpp/CMakeLists.txt. Everything
# downstream -- include paths, compile flags, transitive dependencies, RPATH --
# comes along with that target automatically. That is the entire reason to
# route this through CMake rather than hand-written compiler flags.
#
# Options can be set from pyproject.toml so an ordinary `pip install .` picks
# them up:
#
#   [tool.scikit-build.cmake.define]
#   TPP_USE_SYSTEM_EIGEN = "ON"
#
# or per-build from the command line, without editing any file:
#
#   pip install . -C cmake.define.TPP_USE_SYSTEM_EIGEN=ON
#   SKBUILD_CMAKE_DEFINE="TPP_USE_SYSTEM_EIGEN=ON" pip install .

include_guard(GLOBAL)

# Collects every external target the extension should link against. src/cpp
# reads this variable, so adding a library never requires editing that file.
set(TPP_EXTERNAL_LINK_TARGETS "" CACHE INTERNAL "External targets to link into the extension")

function(tpp_register_external_target TARGET_NAME)
    if(NOT TARGET ${TARGET_NAME})
        message(FATAL_ERROR "tpp_register_external_target: '${TARGET_NAME}' is not a CMake target.")
    endif()
    set(TPP_EXTERNAL_LINK_TARGETS ${TPP_EXTERNAL_LINK_TARGETS} ${TARGET_NAME}
        CACHE INTERNAL "External targets to link into the extension")
    message(STATUS "Extension will link external target: ${TARGET_NAME}")
endfunction()

# ---------------------------------------------------------------------------
# Pattern 1 -- find_package(): the library is already installed
# ---------------------------------------------------------------------------
#
# Use when the library ships a CMake config package or CMake has a bundled
# Find module for it. This is the cheapest option and the right default for
# anything available from a package manager.
#
# Prefer `CONFIG` mode: it consumes the library's own exported targets, which
# carry the correct include dirs and transitive deps. Only fall back to MODULE
# mode (a FindFoo.cmake) for libraries too old to export their own config.
#
# Worked example: Eigen3, a common numerical dependency.
#   sudo apt install libeigen3-dev      # or: conda install eigen
#   pip install . -C cmake.define.TPP_USE_SYSTEM_EIGEN=ON

option(TPP_USE_SYSTEM_EIGEN "Link the extension against a system-installed Eigen3" OFF)

if(TPP_USE_SYSTEM_EIGEN)
    find_package(Eigen3 3.3 REQUIRED NO_MODULE)
    tpp_register_external_target(Eigen3::Eigen)

    # Tell the C++ sources the dependency is available, so bindings.cpp can
    # guard Eigen-specific code behind #ifdef TPP_HAVE_EIGEN.
    add_compile_definitions(TPP_HAVE_EIGEN=1)
endif()

# ---------------------------------------------------------------------------
# Pattern 2 -- FetchContent: pinned upstream source, built with your flags
# ---------------------------------------------------------------------------
#
# Use when the library is not packaged, when you need a specific commit, or
# when you need it compiled with the same flags and ABI as your extension
# (crucial when C++ types cross the boundary between them).
#
# ALWAYS pin GIT_TAG to a tag or full commit SHA. Pinning to a branch makes
# your build non-reproducible and lets an upstream push break your wheels.
#
# Worked example: fmt, a small well-behaved CMake library.
#   pip install . -C cmake.define.TPP_FETCH_FMT=ON

option(TPP_FETCH_FMT "Fetch and build the fmt library from source" OFF)

if(TPP_FETCH_FMT)
    include(FetchContent)

    FetchContent_Declare(
        fmt
        GIT_REPOSITORY https://github.com/fmtlib/fmt.git
        GIT_TAG        11.0.2          # pinned release tag, never a branch
        GIT_SHALLOW    TRUE
        # Skip the update step on reconfigure; the tag is immutable anyway.
        UPDATE_DISCONNECTED TRUE
    )

    # Keep the dependency's own tests and installs out of our build and out of
    # our wheel. Most CMake projects honour options like these; check the
    # library's CMakeLists for its actual option names.
    set(FMT_TEST OFF CACHE BOOL "" FORCE)
    set(FMT_DOC OFF CACHE BOOL "" FORCE)
    set(FMT_INSTALL OFF CACHE BOOL "" FORCE)

    FetchContent_MakeAvailable(fmt)

    # Static linking keeps the wheel self-contained: no second .so to bundle
    # and no loader path to get right.
    tpp_register_external_target(fmt::fmt-header-only)
    add_compile_definitions(TPP_HAVE_FMT=1)
endif()

# ---------------------------------------------------------------------------
# Pattern 3 -- add_subdirectory(): vendored source or git submodule
# ---------------------------------------------------------------------------
#
# Use when the source lives in this repository, typically added with:
#   git submodule add https://github.com/org/mylib.git lib/mylib
#   git submodule update --init --recursive
#
# This gives the most control and the most reproducible build, at the cost of
# carrying the source. It is also the pattern to use for a proprietary or
# internal library that is not publicly fetchable.
#
# The loop below picks up any directory under lib/ that has its own
# CMakeLists.txt, so adding a submodule needs no edit to this file.

option(TPP_USE_VENDORED_LIBS "Build every CMake project found under lib/" OFF)

if(TPP_USE_VENDORED_LIBS)
    file(GLOB _vendored_candidates
         LIST_DIRECTORIES true
         "${PROJECT_SOURCE_DIR}/lib/*")

    set(_found_any FALSE)
    foreach(_candidate IN LISTS _vendored_candidates)
        if(IS_DIRECTORY "${_candidate}" AND EXISTS "${_candidate}/CMakeLists.txt")
            get_filename_component(_vendored_name "${_candidate}" NAME)
            message(STATUS "Adding vendored library: ${_vendored_name}")
            # EXCLUDE_FROM_ALL keeps targets we never link out of the build.
            add_subdirectory("${_candidate}" "${CMAKE_BINARY_DIR}/lib/${_vendored_name}" EXCLUDE_FROM_ALL)
            set(_found_any TRUE)

            # Register the conventional target name if the library provides it.
            # Adjust to match the actual exported target of your library.
            if(TARGET ${_vendored_name})
                tpp_register_external_target(${_vendored_name})
            endif()
        endif()
    endforeach()

    if(NOT _found_any)
        message(WARNING
            "TPP_USE_VENDORED_LIBS=ON but no CMake project was found under lib/.\n"
            "  Add one with: git submodule add <url> lib/<name>")
    endif()
endif()

# ---------------------------------------------------------------------------
# Wiring a plain C library that has no CMake support at all
# ---------------------------------------------------------------------------
#
# Some C libraries ship only headers and a .a/.so, or only a pkg-config file.
# Wrap them in an IMPORTED target once, and the rest of the build treats them
# like any other modern CMake dependency.
#
# Via pkg-config (preferred when a .pc file exists):
#
#   find_package(PkgConfig REQUIRED)
#   pkg_check_modules(MYLIB REQUIRED IMPORTED_TARGET mylib>=1.2)
#   tpp_register_external_target(PkgConfig::MYLIB)
#
# Fully manual (no CMake, no pkg-config):
#
#   find_path(MYLIB_INCLUDE_DIR mylib.h HINTS /opt/mylib/include)
#   find_library(MYLIB_LIBRARY NAMES mylib HINTS /opt/mylib/lib)
#   if(NOT MYLIB_INCLUDE_DIR OR NOT MYLIB_LIBRARY)
#       message(FATAL_ERROR "mylib not found; set -DCMAKE_PREFIX_PATH=/opt/mylib")
#   endif()
#   add_library(mylib::mylib UNKNOWN IMPORTED)
#   set_target_properties(mylib::mylib PROPERTIES
#       IMPORTED_LOCATION "${MYLIB_LIBRARY}"
#       INTERFACE_INCLUDE_DIRECTORIES "${MYLIB_INCLUDE_DIR}")
#   tpp_register_external_target(mylib::mylib)
#
# Remember: C headers need `extern "C"` when included from C++. If the header
# does not already guard itself with __cplusplus, wrap the include:
#
#   extern "C" {
#   #include <mylib.h>
#   }
#
# If you link a *shared* third-party library, its .so must also be copied into
# the wheel beside the extension, or the wheel will only import on machines
# that happen to have it installed. On Linux/macOS the standard tools for this
# are `auditwheel repair` and `delocate-wheel`, which cibuildwheel runs for you
# automatically. Static linking sidesteps the problem entirely.
