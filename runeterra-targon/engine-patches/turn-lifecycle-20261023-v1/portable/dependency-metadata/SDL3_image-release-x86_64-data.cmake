########### AGGREGATED COMPONENTS AND DEPENDENCIES FOR THE MULTI CONFIG #####################
#############################################################################################

set(sdl_image_COMPONENT_NAMES "")
if(DEFINED sdl_image_FIND_DEPENDENCY_NAMES)
  list(APPEND sdl_image_FIND_DEPENDENCY_NAMES SDL3 PNG)
  list(REMOVE_DUPLICATES sdl_image_FIND_DEPENDENCY_NAMES)
else()
  set(sdl_image_FIND_DEPENDENCY_NAMES SDL3 PNG)
endif()
set(SDL3_FIND_MODE "NO_MODULE")
set(PNG_FIND_MODE "NO_MODULE")

########### VARIABLES #######################################################################
#############################################################################################
set(sdl_image_PACKAGE_FOLDER_RELEASE "<SDK_ROOT>/conan-home/p/sdl_i44042adf09a1b/p")
set(sdl_image_BUILD_MODULES_PATHS_RELEASE )


set(sdl_image_INCLUDE_DIRS_RELEASE "${sdl_image_PACKAGE_FOLDER_RELEASE}/include")
set(sdl_image_RES_DIRS_RELEASE )
set(sdl_image_DEFINITIONS_RELEASE )
set(sdl_image_SHARED_LINK_FLAGS_RELEASE )
set(sdl_image_EXE_LINK_FLAGS_RELEASE )
set(sdl_image_OBJECTS_RELEASE )
set(sdl_image_COMPILE_DEFINITIONS_RELEASE )
set(sdl_image_COMPILE_OPTIONS_C_RELEASE )
set(sdl_image_COMPILE_OPTIONS_CXX_RELEASE )
set(sdl_image_LIB_DIRS_RELEASE "${sdl_image_PACKAGE_FOLDER_RELEASE}/lib")
set(sdl_image_BIN_DIRS_RELEASE "${sdl_image_PACKAGE_FOLDER_RELEASE}/bin")
set(sdl_image_LIBRARY_TYPE_RELEASE SHARED)
set(sdl_image_IS_HOST_WINDOWS_RELEASE 1)
set(sdl_image_LIBS_RELEASE SDL3_image)
set(sdl_image_SYSTEM_LIBS_RELEASE )
set(sdl_image_FRAMEWORK_DIRS_RELEASE )
set(sdl_image_FRAMEWORKS_RELEASE )
set(sdl_image_BUILD_DIRS_RELEASE )
set(sdl_image_NO_SONAME_MODE_RELEASE FALSE)


# COMPOUND VARIABLES
set(sdl_image_COMPILE_OPTIONS_RELEASE)
if (NOT "${sdl_image_COMPILE_OPTIONS_CXX_RELEASE}" STREQUAL "")
    list(APPEND sdl_image_COMPILE_OPTIONS_RELEASE
        "$<$<COMPILE_LANGUAGE:CXX>:${sdl_image_COMPILE_OPTIONS_CXX_RELEASE}>")
endif ()
if (NOT "${sdl_image_COMPILE_OPTIONS_C_RELEASE}" STREQUAL "")
    list(APPEND sdl_image_COMPILE_OPTIONS_RELEASE
        "$<$<COMPILE_LANGUAGE:C>:${sdl_image_COMPILE_OPTIONS_C_RELEASE}>")
endif ()
set(sdl_image_LINKER_FLAGS_RELEASE)
if (NOT "${sdl_image_SHARED_LINK_FLAGS_RELEASE}" STREQUAL "")
    list(APPEND sdl_image_LINKER_FLAGS_RELEASE
        "$<$<OR:$<STREQUAL:$<TARGET_PROPERTY:TYPE>,SHARED_LIBRARY>,$<STREQUAL:$<TARGET_PROPERTY:TYPE>,MODULE_LIBRARY>>:${sdl_image_SHARED_LINK_FLAGS_RELEASE}>")
endif ()
if (NOT "${sdl_image_EXE_LINK_FLAGS_RELEASE}" STREQUAL "")
    list(APPEND sdl_image_LINKER_FLAGS_RELEASE
        "$<$<STREQUAL:$<TARGET_PROPERTY:TYPE>,EXECUTABLE>:${sdl_image_EXE_LINK_FLAGS_RELEASE}>")
endif ()


set(sdl_image_COMPONENTS_RELEASE )