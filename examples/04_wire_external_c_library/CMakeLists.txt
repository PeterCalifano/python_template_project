# Self-contained demonstration of Pattern 3 (add_subdirectory / vendored source).
#
# This builds a real pybind11 module that links a real C library, so you can
# run it and see the whole chain work before adapting it to your own project.
# In the actual template, the equivalent wiring lives in
# cmake/HandleExternalLibs.cmake and src/cpp/CMakeLists.txt.

cmake_minimum_required(VERSION 3.20...3.31)
project(mylib_bindings VERSION 1.0.0 LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

set(PYBIND11_FINDPYTHON ON)
find_package(Python 3.10 REQUIRED COMPONENTS Interpreter Development.Module)

find_package(pybind11 CONFIG QUIET)
if(NOT pybind11_FOUND)
    execute_process(
        COMMAND "${Python_EXECUTABLE}" -m pybind11 --cmakedir
        OUTPUT_VARIABLE _pybind11_cmakedir
        OUTPUT_STRIP_TRAILING_WHITESPACE
        ERROR_QUIET)
    find_package(pybind11 CONFIG REQUIRED PATHS "${_pybind11_cmakedir}" NO_DEFAULT_PATH)
endif()

# --- Pattern 3: the external library is source inside this tree -------------
# In a real project this directory is typically a git submodule:
#     git submodule add https://github.com/org/mylib.git lib/mylib
add_subdirectory(mylib)

pybind11_add_module(_mylib MODULE bindings_mylib.cpp)

# Linking the target is the entire integration step. The include directory,
# the position-independent flag, and any transitive dependencies all arrive
# through this one line -- that is what modern CMake targets buy you, and why
# this is preferable to hand-written -I/-L/-l flags.
target_link_libraries(_mylib PRIVATE mylib::mylib)

# Drop the built module beside this file so demo.py can import it directly.
set_target_properties(_mylib PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}")
