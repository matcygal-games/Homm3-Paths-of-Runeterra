########### AGGREGATED COMPONENTS AND DEPENDENCIES FOR THE MULTI CONFIG #####################
#############################################################################################

set(sdl_ttf_COMPONENT_NAMES "")
if(DEFINED sdl_ttf_FIND_DEPENDENCY_NAMES)
  list(APPEND sdl_ttf_FIND_DEPENDENCY_NAMES plutosvg freetype SDL3)
  list(REMOVE_DUPLICATES sdl_ttf_FIND_DEPENDENCY_NAMES)
else()
  set(sdl_ttf_FIND_DEPENDENCY_NAMES plutosvg freetype SDL3)
endif()
set(plutosvg_FIND_MODE "NO_MODULE")
set(freetype_FIND_MODE "NO_MODULE")
set(SDL3_FIND_MODE "NO_MODULE")

########### VARIABLES #######################################################################
#############################################################################################
set(sdl_ttf_PACKAGE_FOLDER_RELEASE "<SDK_ROOT>/conan-home/p/sdl_td9fee9bb38b98/p")
set(sdl_ttf_BUILD_MODULES_PATHS_RELEASE )


set(sdl_ttf_INCLUDE_DIRS_RELEASE "${sdl_ttf_PACKAGE_FOLDER_RELEASE}/include")
set(sdl_ttf_RES_DIRS_RELEASE )
set(sdl_ttf_DEFINITIONS_RELEASE )
set(sdl_ttf_SHARED_LINK_FLAGS_RELEASE )
set(sdl_ttf_EXE_LINK_FLAGS_RELEASE )
set(sdl_ttf_OBJECTS_RELEASE )
set(sdl_ttf_COMPILE_DEFINITIONS_RELEASE )
set(sdl_ttf_COMPILE_OPTIONS_C_RELEASE )
set(sdl_ttf_COMPILE_OPTIONS_CXX_RELEASE )
set(sdl_ttf_LIB_DIRS_RELEASE "${sdl_ttf_PACKAGE_FOLDER_RELEASE}/lib")
set(sdl_ttf_BIN_DIRS_RELEASE "${sdl_ttf_PACKAGE_FOLDER_RELEASE}/bin")
set(sdl_ttf_LIBRARY_TYPE_RELEASE SHARED)
set(sdl_ttf_IS_HOST_WINDOWS_RELEASE 1)
set(sdl_ttf_LIBS_RELEASE SDL3_ttf)
set(sdl_ttf_SYSTEM_LIBS_RELEASE )
set(sdl_ttf_FRAMEWORK_DIRS_RELEASE )
set(sdl_ttf_FRAMEWORKS_RELEASE )
set(sdl_ttf_BUILD_DIRS_RELEASE )
set(sdl_ttf_NO_SONAME_MODE_RELEASE FALSE)


# COMPOUND VARIABLES
set(sdl_ttf_COMPILE_OPTIONS_RELEASE)
if (NOT "${sdl_ttf_COMPILE_OPTIONS_CXX_RELEASE}" STREQUAL "")
    list(APPEND sdl_ttf_COMPILE_OPTIONS_RELEASE
        "$<$<COMPILE_LANGUAGE:CXX>:${sdl_ttf_COMPILE_OPTIONS_CXX_RELEASE}>")
endif ()
if (NOT "${sdl_ttf_COMPILE_OPTIONS_C_RELEASE}" STREQUAL "")
    list(APPEND sdl_ttf_COMPILE_OPTIONS_RELEASE
        "$<$<COMPILE_LANGUAGE:C>:${sdl_ttf_COMPILE_OPTIONS_C_RELEASE}>")
endif ()
set(sdl_ttf_LINKER_FLAGS_RELEASE)
if (NOT "${sdl_ttf_SHARED_LINK_FLAGS_RELEASE}" STREQUAL "")
    list(APPEND sdl_ttf_LINKER_FLAGS_RELEASE
        "$<$<OR:$<STREQUAL:$<TARGET_PROPERTY:TYPE>,SHARED_LIBRARY>,$<STREQUAL:$<TARGET_PROPERTY:TYPE>,MODULE_LIBRARY>>:${sdl_ttf_SHARED_LINK_FLAGS_RELEASE}>")
endif ()
if (NOT "${sdl_ttf_EXE_LINK_FLAGS_RELEASE}" STREQUAL "")
    list(APPEND sdl_ttf_LINKER_FLAGS_RELEASE
        "$<$<STREQUAL:$<TARGET_PROPERTY:TYPE>,EXECUTABLE>:${sdl_ttf_EXE_LINK_FLAGS_RELEASE}>")
endif ()


set(sdl_ttf_COMPONENTS_RELEASE )