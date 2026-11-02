# Avoid multiple calls to find_package to append duplicated properties to the targets
include_guard()########### VARIABLES #######################################################################
#############################################################################################
set(plutosvg_FRAMEWORKS_FOUND_RELEASE "") # Will be filled later
conan_find_apple_frameworks(plutosvg_FRAMEWORKS_FOUND_RELEASE "${plutosvg_FRAMEWORKS_RELEASE}" "${plutosvg_FRAMEWORK_DIRS_RELEASE}")

set(plutosvg_LIBRARIES_TARGETS "") # Will be filled later


######## Create an interface target to contain all the dependencies (frameworks, system and conan deps)
if(NOT TARGET plutosvg_DEPS_TARGET)
    add_library(plutosvg_DEPS_TARGET INTERFACE IMPORTED)
endif()

set_property(TARGET plutosvg_DEPS_TARGET
             APPEND PROPERTY INTERFACE_LINK_LIBRARIES
             $<$<CONFIG:Release>:${plutosvg_FRAMEWORKS_FOUND_RELEASE}>
             $<$<CONFIG:Release>:${plutosvg_SYSTEM_LIBS_RELEASE}>
             $<$<CONFIG:Release>:Freetype::Freetype>)

####### Find the libraries declared in cpp_info.libs, create an IMPORTED target for each one and link the
####### plutosvg_DEPS_TARGET to all of them
conan_package_library_targets("${plutosvg_LIBS_RELEASE}"    # libraries
                              "${plutosvg_LIB_DIRS_RELEASE}" # package_libdir
                              "${plutosvg_BIN_DIRS_RELEASE}" # package_bindir
                              "${plutosvg_LIBRARY_TYPE_RELEASE}"
                              "${plutosvg_IS_HOST_WINDOWS_RELEASE}"
                              plutosvg_DEPS_TARGET
                              plutosvg_LIBRARIES_TARGETS  # out_libraries_targets
                              "_RELEASE"
                              "plutosvg"    # package_name
                              "${plutosvg_NO_SONAME_MODE_RELEASE}")  # soname

# FIXME: What is the result of this for multi-config? All configs adding themselves to path?
set(CMAKE_MODULE_PATH ${plutosvg_BUILD_DIRS_RELEASE} ${CMAKE_MODULE_PATH})

########## GLOBAL TARGET PROPERTIES Release ########################################
    set_property(TARGET plutosvg::plutosvg
                 APPEND PROPERTY INTERFACE_LINK_LIBRARIES
                 $<$<CONFIG:Release>:${plutosvg_OBJECTS_RELEASE}>
                 $<$<CONFIG:Release>:${plutosvg_LIBRARIES_TARGETS}>
                 )

    if("${plutosvg_LIBS_RELEASE}" STREQUAL "")
        # If the package is not declaring any "cpp_info.libs" the package deps, system libs,
        # frameworks etc are not linked to the imported targets and we need to do it to the
        # global target
        set_property(TARGET plutosvg::plutosvg
                     APPEND PROPERTY INTERFACE_LINK_LIBRARIES
                     plutosvg_DEPS_TARGET)
    endif()

    set_property(TARGET plutosvg::plutosvg
                 APPEND PROPERTY INTERFACE_LINK_OPTIONS
                 $<$<CONFIG:Release>:${plutosvg_LINKER_FLAGS_RELEASE}>)
    set_property(TARGET plutosvg::plutosvg
                 APPEND PROPERTY INTERFACE_INCLUDE_DIRECTORIES
                 $<$<CONFIG:Release>:${plutosvg_INCLUDE_DIRS_RELEASE}>)
    # Necessary to find LINK shared libraries in Linux
    set_property(TARGET plutosvg::plutosvg
                 APPEND PROPERTY INTERFACE_LINK_DIRECTORIES
                 $<$<CONFIG:Release>:${plutosvg_LIB_DIRS_RELEASE}>)
    set_property(TARGET plutosvg::plutosvg
                 APPEND PROPERTY INTERFACE_COMPILE_DEFINITIONS
                 $<$<CONFIG:Release>:${plutosvg_COMPILE_DEFINITIONS_RELEASE}>)
    set_property(TARGET plutosvg::plutosvg
                 APPEND PROPERTY INTERFACE_COMPILE_OPTIONS
                 $<$<CONFIG:Release>:${plutosvg_COMPILE_OPTIONS_RELEASE}>)

########## For the modules (FindXXX)
set(plutosvg_LIBRARIES_RELEASE plutosvg::plutosvg)
