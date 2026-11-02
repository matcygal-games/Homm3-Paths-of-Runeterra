# Avoid multiple calls to find_package to append duplicated properties to the targets
include_guard()########### VARIABLES #######################################################################
#############################################################################################
set(sdl_ttf_FRAMEWORKS_FOUND_RELEASE "") # Will be filled later
conan_find_apple_frameworks(sdl_ttf_FRAMEWORKS_FOUND_RELEASE "${sdl_ttf_FRAMEWORKS_RELEASE}" "${sdl_ttf_FRAMEWORK_DIRS_RELEASE}")

set(sdl_ttf_LIBRARIES_TARGETS "") # Will be filled later


######## Create an interface target to contain all the dependencies (frameworks, system and conan deps)
if(NOT TARGET sdl_ttf_DEPS_TARGET)
    add_library(sdl_ttf_DEPS_TARGET INTERFACE IMPORTED)
endif()

set_property(TARGET sdl_ttf_DEPS_TARGET
             APPEND PROPERTY INTERFACE_LINK_LIBRARIES
             $<$<CONFIG:Release>:${sdl_ttf_FRAMEWORKS_FOUND_RELEASE}>
             $<$<CONFIG:Release>:${sdl_ttf_SYSTEM_LIBS_RELEASE}>
             $<$<CONFIG:Release>:plutosvg::plutosvg;Freetype::Freetype;sdl::sdl>)

####### Find the libraries declared in cpp_info.libs, create an IMPORTED target for each one and link the
####### sdl_ttf_DEPS_TARGET to all of them
conan_package_library_targets("${sdl_ttf_LIBS_RELEASE}"    # libraries
                              "${sdl_ttf_LIB_DIRS_RELEASE}" # package_libdir
                              "${sdl_ttf_BIN_DIRS_RELEASE}" # package_bindir
                              "${sdl_ttf_LIBRARY_TYPE_RELEASE}"
                              "${sdl_ttf_IS_HOST_WINDOWS_RELEASE}"
                              sdl_ttf_DEPS_TARGET
                              sdl_ttf_LIBRARIES_TARGETS  # out_libraries_targets
                              "_RELEASE"
                              "sdl_ttf"    # package_name
                              "${sdl_ttf_NO_SONAME_MODE_RELEASE}")  # soname

# FIXME: What is the result of this for multi-config? All configs adding themselves to path?
set(CMAKE_MODULE_PATH ${sdl_ttf_BUILD_DIRS_RELEASE} ${CMAKE_MODULE_PATH})

########## GLOBAL TARGET PROPERTIES Release ########################################
    set_property(TARGET SDL3_ttf::SDL3_ttf
                 APPEND PROPERTY INTERFACE_LINK_LIBRARIES
                 $<$<CONFIG:Release>:${sdl_ttf_OBJECTS_RELEASE}>
                 $<$<CONFIG:Release>:${sdl_ttf_LIBRARIES_TARGETS}>
                 )

    if("${sdl_ttf_LIBS_RELEASE}" STREQUAL "")
        # If the package is not declaring any "cpp_info.libs" the package deps, system libs,
        # frameworks etc are not linked to the imported targets and we need to do it to the
        # global target
        set_property(TARGET SDL3_ttf::SDL3_ttf
                     APPEND PROPERTY INTERFACE_LINK_LIBRARIES
                     sdl_ttf_DEPS_TARGET)
    endif()

    set_property(TARGET SDL3_ttf::SDL3_ttf
                 APPEND PROPERTY INTERFACE_LINK_OPTIONS
                 $<$<CONFIG:Release>:${sdl_ttf_LINKER_FLAGS_RELEASE}>)
    set_property(TARGET SDL3_ttf::SDL3_ttf
                 APPEND PROPERTY INTERFACE_INCLUDE_DIRECTORIES
                 $<$<CONFIG:Release>:${sdl_ttf_INCLUDE_DIRS_RELEASE}>)
    # Necessary to find LINK shared libraries in Linux
    set_property(TARGET SDL3_ttf::SDL3_ttf
                 APPEND PROPERTY INTERFACE_LINK_DIRECTORIES
                 $<$<CONFIG:Release>:${sdl_ttf_LIB_DIRS_RELEASE}>)
    set_property(TARGET SDL3_ttf::SDL3_ttf
                 APPEND PROPERTY INTERFACE_COMPILE_DEFINITIONS
                 $<$<CONFIG:Release>:${sdl_ttf_COMPILE_DEFINITIONS_RELEASE}>)
    set_property(TARGET SDL3_ttf::SDL3_ttf
                 APPEND PROPERTY INTERFACE_COMPILE_OPTIONS
                 $<$<CONFIG:Release>:${sdl_ttf_COMPILE_OPTIONS_RELEASE}>)

########## For the modules (FindXXX)
set(sdl_ttf_LIBRARIES_RELEASE SDL3_ttf::SDL3_ttf)
