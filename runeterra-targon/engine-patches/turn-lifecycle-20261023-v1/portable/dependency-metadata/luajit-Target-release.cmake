# Avoid multiple calls to find_package to append duplicated properties to the targets
include_guard()########### VARIABLES #######################################################################
#############################################################################################
set(luajit_FRAMEWORKS_FOUND_RELEASE "") # Will be filled later
conan_find_apple_frameworks(luajit_FRAMEWORKS_FOUND_RELEASE "${luajit_FRAMEWORKS_RELEASE}" "${luajit_FRAMEWORK_DIRS_RELEASE}")

set(luajit_LIBRARIES_TARGETS "") # Will be filled later


######## Create an interface target to contain all the dependencies (frameworks, system and conan deps)
if(NOT TARGET luajit_DEPS_TARGET)
    add_library(luajit_DEPS_TARGET INTERFACE IMPORTED)
endif()

set_property(TARGET luajit_DEPS_TARGET
             APPEND PROPERTY INTERFACE_LINK_LIBRARIES
             $<$<CONFIG:Release>:${luajit_FRAMEWORKS_FOUND_RELEASE}>
             $<$<CONFIG:Release>:${luajit_SYSTEM_LIBS_RELEASE}>
             $<$<CONFIG:Release>:>)

####### Find the libraries declared in cpp_info.libs, create an IMPORTED target for each one and link the
####### luajit_DEPS_TARGET to all of them
conan_package_library_targets("${luajit_LIBS_RELEASE}"    # libraries
                              "${luajit_LIB_DIRS_RELEASE}" # package_libdir
                              "${luajit_BIN_DIRS_RELEASE}" # package_bindir
                              "${luajit_LIBRARY_TYPE_RELEASE}"
                              "${luajit_IS_HOST_WINDOWS_RELEASE}"
                              luajit_DEPS_TARGET
                              luajit_LIBRARIES_TARGETS  # out_libraries_targets
                              "_RELEASE"
                              "luajit"    # package_name
                              "${luajit_NO_SONAME_MODE_RELEASE}")  # soname

# FIXME: What is the result of this for multi-config? All configs adding themselves to path?
set(CMAKE_MODULE_PATH ${luajit_BUILD_DIRS_RELEASE} ${CMAKE_MODULE_PATH})

########## GLOBAL TARGET PROPERTIES Release ########################################
    set_property(TARGET luajit::luajit
                 APPEND PROPERTY INTERFACE_LINK_LIBRARIES
                 $<$<CONFIG:Release>:${luajit_OBJECTS_RELEASE}>
                 $<$<CONFIG:Release>:${luajit_LIBRARIES_TARGETS}>
                 )

    if("${luajit_LIBS_RELEASE}" STREQUAL "")
        # If the package is not declaring any "cpp_info.libs" the package deps, system libs,
        # frameworks etc are not linked to the imported targets and we need to do it to the
        # global target
        set_property(TARGET luajit::luajit
                     APPEND PROPERTY INTERFACE_LINK_LIBRARIES
                     luajit_DEPS_TARGET)
    endif()

    set_property(TARGET luajit::luajit
                 APPEND PROPERTY INTERFACE_LINK_OPTIONS
                 $<$<CONFIG:Release>:${luajit_LINKER_FLAGS_RELEASE}>)
    set_property(TARGET luajit::luajit
                 APPEND PROPERTY INTERFACE_INCLUDE_DIRECTORIES
                 $<$<CONFIG:Release>:${luajit_INCLUDE_DIRS_RELEASE}>)
    # Necessary to find LINK shared libraries in Linux
    set_property(TARGET luajit::luajit
                 APPEND PROPERTY INTERFACE_LINK_DIRECTORIES
                 $<$<CONFIG:Release>:${luajit_LIB_DIRS_RELEASE}>)
    set_property(TARGET luajit::luajit
                 APPEND PROPERTY INTERFACE_COMPILE_DEFINITIONS
                 $<$<CONFIG:Release>:${luajit_COMPILE_DEFINITIONS_RELEASE}>)
    set_property(TARGET luajit::luajit
                 APPEND PROPERTY INTERFACE_COMPILE_OPTIONS
                 $<$<CONFIG:Release>:${luajit_COMPILE_OPTIONS_RELEASE}>)

########## For the modules (FindXXX)
set(luajit_LIBRARIES_RELEASE luajit::luajit)
