########## MACROS ###########################################################################
#############################################################################################

# Requires CMake > 3.15
if(${CMAKE_VERSION} VERSION_LESS "3.15")
    message(FATAL_ERROR "The 'CMakeDeps' generator only works with CMake >= 3.15")
endif()

if(luajit_FIND_QUIETLY)
    set(luajit_MESSAGE_MODE VERBOSE)
else()
    set(luajit_MESSAGE_MODE STATUS)
endif()

include(${CMAKE_CURRENT_LIST_DIR}/cmakedeps_macros.cmake)
include(${CMAKE_CURRENT_LIST_DIR}/luajitTargets.cmake)
include(CMakeFindDependencyMacro)

check_build_type_defined()

foreach(_DEPENDENCY ${luajit_FIND_DEPENDENCY_NAMES} )
    # Check that we have not already called a find_package with the transitive dependency
    if(NOT ${_DEPENDENCY}_FOUND)
        find_dependency(${_DEPENDENCY} REQUIRED ${${_DEPENDENCY}_FIND_MODE})
    endif()
endforeach()

set(luajit_VERSION_STRING "7ff85518540617c0f97c4720558bb21c245994a8")
set(luajit_INCLUDE_DIRS ${luajit_INCLUDE_DIRS_RELEASE} )
set(luajit_INCLUDE_DIR ${luajit_INCLUDE_DIRS_RELEASE} )
set(luajit_LIBRARIES ${luajit_LIBRARIES_RELEASE} )
set(luajit_DEFINITIONS ${luajit_DEFINITIONS_RELEASE} )


# Definition of extra CMake variables from cmake_extra_variables


# Only the last installed configuration BUILD_MODULES are included to avoid the collision
foreach(_BUILD_MODULE ${luajit_BUILD_MODULES_PATHS_RELEASE} )
    message(${luajit_MESSAGE_MODE} "Conan: Including build module from '${_BUILD_MODULE}'")
    include(${_BUILD_MODULE})
endforeach()


