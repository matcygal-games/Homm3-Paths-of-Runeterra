########### AGGREGATED COMPONENTS AND DEPENDENCIES FOR THE MULTI CONFIG #####################
#############################################################################################

set(sdl_mixer_COMPONENT_NAMES "")
if(DEFINED sdl_mixer_FIND_DEPENDENCY_NAMES)
  list(APPEND sdl_mixer_FIND_DEPENDENCY_NAMES flac opusfile mpg123 Ogg SDL3)
  list(REMOVE_DUPLICATES sdl_mixer_FIND_DEPENDENCY_NAMES)
else()
  set(sdl_mixer_FIND_DEPENDENCY_NAMES flac opusfile mpg123 Ogg SDL3)
endif()
set(flac_FIND_MODE "NO_MODULE")
set(opusfile_FIND_MODE "NO_MODULE")
set(mpg123_FIND_MODE "NO_MODULE")
set(Ogg_FIND_MODE "NO_MODULE")
set(SDL3_FIND_MODE "NO_MODULE")

########### VARIABLES #######################################################################
#############################################################################################
set(sdl_mixer_PACKAGE_FOLDER_RELEASE "<SDK_ROOT>/conan-home/p/sdl_ma71c9f6f2fcfe/p")
set(sdl_mixer_BUILD_MODULES_PATHS_RELEASE )


set(sdl_mixer_INCLUDE_DIRS_RELEASE "${sdl_mixer_PACKAGE_FOLDER_RELEASE}/include")
set(sdl_mixer_RES_DIRS_RELEASE )
set(sdl_mixer_DEFINITIONS_RELEASE )
set(sdl_mixer_SHARED_LINK_FLAGS_RELEASE )
set(sdl_mixer_EXE_LINK_FLAGS_RELEASE )
set(sdl_mixer_OBJECTS_RELEASE )
set(sdl_mixer_COMPILE_DEFINITIONS_RELEASE )
set(sdl_mixer_COMPILE_OPTIONS_C_RELEASE )
set(sdl_mixer_COMPILE_OPTIONS_CXX_RELEASE )
set(sdl_mixer_LIB_DIRS_RELEASE "${sdl_mixer_PACKAGE_FOLDER_RELEASE}/lib")
set(sdl_mixer_BIN_DIRS_RELEASE "${sdl_mixer_PACKAGE_FOLDER_RELEASE}/bin")
set(sdl_mixer_LIBRARY_TYPE_RELEASE SHARED)
set(sdl_mixer_IS_HOST_WINDOWS_RELEASE 1)
set(sdl_mixer_LIBS_RELEASE SDL3_mixer)
set(sdl_mixer_SYSTEM_LIBS_RELEASE )
set(sdl_mixer_FRAMEWORK_DIRS_RELEASE )
set(sdl_mixer_FRAMEWORKS_RELEASE )
set(sdl_mixer_BUILD_DIRS_RELEASE )
set(sdl_mixer_NO_SONAME_MODE_RELEASE FALSE)


# COMPOUND VARIABLES
set(sdl_mixer_COMPILE_OPTIONS_RELEASE)
if (NOT "${sdl_mixer_COMPILE_OPTIONS_CXX_RELEASE}" STREQUAL "")
    list(APPEND sdl_mixer_COMPILE_OPTIONS_RELEASE
        "$<$<COMPILE_LANGUAGE:CXX>:${sdl_mixer_COMPILE_OPTIONS_CXX_RELEASE}>")
endif ()
if (NOT "${sdl_mixer_COMPILE_OPTIONS_C_RELEASE}" STREQUAL "")
    list(APPEND sdl_mixer_COMPILE_OPTIONS_RELEASE
        "$<$<COMPILE_LANGUAGE:C>:${sdl_mixer_COMPILE_OPTIONS_C_RELEASE}>")
endif ()
set(sdl_mixer_LINKER_FLAGS_RELEASE)
if (NOT "${sdl_mixer_SHARED_LINK_FLAGS_RELEASE}" STREQUAL "")
    list(APPEND sdl_mixer_LINKER_FLAGS_RELEASE
        "$<$<OR:$<STREQUAL:$<TARGET_PROPERTY:TYPE>,SHARED_LIBRARY>,$<STREQUAL:$<TARGET_PROPERTY:TYPE>,MODULE_LIBRARY>>:${sdl_mixer_SHARED_LINK_FLAGS_RELEASE}>")
endif ()
if (NOT "${sdl_mixer_EXE_LINK_FLAGS_RELEASE}" STREQUAL "")
    list(APPEND sdl_mixer_LINKER_FLAGS_RELEASE
        "$<$<STREQUAL:$<TARGET_PROPERTY:TYPE>,EXECUTABLE>:${sdl_mixer_EXE_LINK_FLAGS_RELEASE}>")
endif ()


set(sdl_mixer_COMPONENTS_RELEASE )