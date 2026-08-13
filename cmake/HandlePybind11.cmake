# Locate Python and pybind11 for building extension modules.
#
# Under scikit-build-core this "just works" because:
#   * pybind11 is listed in [build-system].requires, so it is installed into
#     the isolated build environment, and
#   * scikit-build-core sets `search.site-packages = true`, which puts that
#     environment's site-packages on CMAKE_PREFIX_PATH.
#
# When configuring this tree with plain CMake (no scikit-build-core), install
# pybind11 into the active environment first, or point CMake at it with
#   -Dpybind11_DIR=$(python -m pybind11 --cmakedir)

include_guard(GLOBAL)

# Ask pybind11 to use CMake's modern FindPython rather than the deprecated
# FindPythonInterp/FindPythonLibs pair. This must be set before find_package.
set(PYBIND11_FINDPYTHON ON)

# Development.Module (not the full Development component) is the correct
# request for extension modules: it does not require a linkable libpython,
# which is what makes manylinux and macOS wheels portable.
find_package(Python 3.10 REQUIRED COMPONENTS Interpreter Development.Module)

find_package(pybind11 CONFIG QUIET)

if(NOT pybind11_FOUND)
    # Fall back to asking the interpreter where pybind11 keeps its CMake
    # config. This covers plain-CMake configuration in an environment where
    # pybind11 is pip-installed but not on CMAKE_PREFIX_PATH.
    execute_process(
        COMMAND "${Python_EXECUTABLE}" -m pybind11 --cmakedir
        OUTPUT_VARIABLE _pybind11_cmakedir
        OUTPUT_STRIP_TRAILING_WHITESPACE
        ERROR_QUIET
        RESULT_VARIABLE _pybind11_query_result)

    if(_pybind11_query_result EQUAL 0 AND EXISTS "${_pybind11_cmakedir}")
        message(STATUS "Found pybind11 via interpreter query: ${_pybind11_cmakedir}")
        find_package(pybind11 CONFIG REQUIRED PATHS "${_pybind11_cmakedir}" NO_DEFAULT_PATH)
    else()
        message(FATAL_ERROR
            "pybind11 was not found.\n"
            "  Install it with:  pip install pybind11\n"
            "  Or point CMake at it:  -Dpybind11_DIR=$(python -m pybind11 --cmakedir)")
    endif()
endif()

message(STATUS "Using Python ${Python_VERSION}: ${Python_EXECUTABLE}")
message(STATUS "Using pybind11 ${pybind11_VERSION} from ${pybind11_DIR}")

# tpp_add_extension(<name> SOURCES <src>... [LINK <target>...])
#
# Thin wrapper over pybind11_add_module that applies this project's conventions
# in one place: the version macro, warning flags, optional LTO, and -- most
# importantly -- installation *into the Python package directory* so the .so
# ships inside the wheel next to the .py files.
function(tpp_add_extension EXTENSION_NAME)
    cmake_parse_arguments(TPP_EXT "" "" "SOURCES;LINK" ${ARGN})

    if(NOT TPP_EXT_SOURCES)
        message(FATAL_ERROR "tpp_add_extension(${EXTENSION_NAME}) requires SOURCES.")
    endif()

    pybind11_add_module(${EXTENSION_NAME} MODULE ${TPP_EXT_SOURCES})

    # Already a quoted string literal, so bindings.cpp must use it directly
    # rather than passing it through a stringify macro.
    target_compile_definitions(${EXTENSION_NAME}
        PRIVATE VERSION_INFO="${TPP_VERSION_FULL}")

    if(TPP_EXT_LINK)
        target_link_libraries(${EXTENSION_NAME} PRIVATE ${TPP_EXT_LINK})
    endif()

    if(MSVC)
        target_compile_options(${EXTENSION_NAME} PRIVATE /W4)
        if(TPP_WARNINGS_AS_ERRORS)
            target_compile_options(${EXTENSION_NAME} PRIVATE /WX)
        endif()
    else()
        target_compile_options(${EXTENSION_NAME} PRIVATE -Wall -Wextra -Wpedantic)
        if(TPP_WARNINGS_AS_ERRORS)
            target_compile_options(${EXTENSION_NAME} PRIVATE -Werror)
        endif()
    endif()

    if(TPP_ENABLE_LTO)
        include(CheckIPOSupported)
        check_ipo_supported(RESULT _ipo_supported OUTPUT _ipo_error)
        if(_ipo_supported)
            set_property(TARGET ${EXTENSION_NAME}
                         PROPERTY INTERPROCEDURAL_OPTIMIZATION TRUE)
        else()
            message(WARNING "LTO requested but unsupported: ${_ipo_error}")
        endif()
    endif()

    # Load any co-installed shared libraries from beside the module itself.
    # Without this, a wheel that bundles a third-party .so would only import
    # when that library also happened to be on the system loader path.
    if(APPLE)
        set_target_properties(${EXTENSION_NAME} PROPERTIES
            INSTALL_RPATH "@loader_path")
    elseif(UNIX)
        set_target_properties(${EXTENSION_NAME} PROPERTIES
            INSTALL_RPATH "$ORIGIN")
    endif()

    # DESTINATION is relative to the wheel's platlib root, so this places the
    # module inside the importable package.
    install(TARGETS ${EXTENSION_NAME}
            LIBRARY DESTINATION ${SKBUILD_PROJECT_NAME}
            RUNTIME DESTINATION ${SKBUILD_PROJECT_NAME})
endfunction()
