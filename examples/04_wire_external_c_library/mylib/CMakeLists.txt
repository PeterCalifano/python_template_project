# Minimal CMake wrapper around a plain C library.
#
# This is what you write when the library itself has no CMake support. If your
# real library already ships a CMake config package, you do not need this file
# at all -- use find_package() (Pattern 1) instead.

cmake_minimum_required(VERSION 3.20)
project(mylib VERSION 1.0.0 LANGUAGES C)

add_library(mylib STATIC mylib.c)

# A static library that will be linked into a Python extension module (a shared
# object) must be compiled position-independent. Omitting this is the classic
# cause of "relocation R_X86_64_PC32 against symbol ... can not be used when
# making a shared object" at link time.
set_target_properties(mylib PROPERTIES POSITION_INDEPENDENT_CODE ON)

# Consumers get the include directory automatically by linking `mylib`.
# BUILD_INTERFACE/INSTALL_INTERFACE keeps the path correct in both the build
# tree and an installed tree.
target_include_directories(mylib
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
        $<INSTALL_INTERFACE:include>)

# Namespaced alias, so consumers can write mylib::mylib whether the library is
# vendored via add_subdirectory or found via find_package.
add_library(mylib::mylib ALIAS mylib)
