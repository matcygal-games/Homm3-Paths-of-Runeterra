########### AGGREGATED COMPONENTS AND DEPENDENCIES FOR THE MULTI CONFIG #####################
#############################################################################################

set(freetype_COMPONENT_NAMES "")
if(DEFINED freetype_FIND_DEPENDENCY_NAMES)
  list(APPEND freetype_FIND_DEPENDENCY_NAMES BZip2 PNG ZLIB)
  list(REMOVE_DUPLICATES freetype_FIND_DEPENDENCY_NAMES)
else()
  set(freetype_FIND_DEPENDENCY_NAMES BZip2 PNG ZLIB)
endif()
set(BZip2_FIND_MODE "MODULE")
set(PNG_FIND_MODE "MODULE")
set(ZLIB_FIND_MODE "MODULE")

########### VARIABLES #######################################################################
#############################################################################################
set(freetype_PACKAGE_FOLDER_RELEASE "<SDK_ROOT>/conan-home/p/freetf9f0ea006fb2c/p")
set(freetype_BUILD_MODULES_PATHS_RELEASE "${freetype_PACKAGE_FOLDER_RELEASE}/lib/cmake/conan-official-freetype-variables.cmake")


set(freetype_INCLUDE_DIRS_RELEASE )
set(freetype_RES_DIRS_RELEASE )
set(freetype_DEFINITIONS_RELEASE )
set(freetype_SHARED_LINK_FLAGS_RELEASE )
set(freetype_EXE_LINK_FLAGS_RELEASE )
set(freetype_OBJECTS_RELEASE )
set(freetype_COMPILE_DEFINITIONS_RELEASE )
set(freetype_COMPILE_OPTIONS_C_RELEASE )
set(freetype_COMPILE_OPTIONS_CXX_RELEASE )
set(freetype_LIB_DIRS_RELEASE "${freetype_PACKAGE_FOLDER_RELEASE}/lib")
set(freetype_BIN_DIRS_RELEASE )
set(freetype_LIBRARY_TYPE_RELEASE STATIC)
set(freetype_IS_HOST_WINDOWS_RELEASE 1)
set(freetype_LIBS_RELEASE )
set(freetype_SYSTEM_LIBS_RELEASE )
set(freetype_FRAMEWORK_DIRS_RELEASE )
set(freetype_FRAMEWORKS_RELEASE )
set(freetype_BUILD_DIRS_RELEASE )
set(freetype_NO_SONAME_MODE_RELEASE FALSE)


# COMPOUND VARIABLES
set(freetype_COMPILE_OPTIONS_RELEASE)
if (NOT "${freetype_COMPILE_OPTIONS_CXX_RELEASE}" STREQUAL "")
    list(APPEND freetype_COMPILE_OPTIONS_RELEASE
        "$<$<COMPILE_LANGUAGE:CXX>:${freetype_COMPILE_OPTIONS_CXX_RELEASE}>")
endif ()
if (NOT "${freetype_COMPILE_OPTIONS_C_RELEASE}" STREQUAL "")
    list(APPEND freetype_COMPILE_OPTIONS_RELEASE
        "$<$<COMPILE_LANGUAGE:C>:${freetype_COMPILE_OPTIONS_C_RELEASE}>")
endif ()
set(freetype_LINKER_FLAGS_RELEASE)
if (NOT "${freetype_SHARED_LINK_FLAGS_RELEASE}" STREQUAL "")
    list(APPEND freetype_LINKER_FLAGS_RELEASE
        "$<$<OR:$<STREQUAL:$<TARGET_PROPERTY:TYPE>,SHARED_LIBRARY>,$<STREQUAL:$<TARGET_PROPERTY:TYPE>,MODULE_LIBRARY>>:${freetype_SHARED_LINK_FLAGS_RELEASE}>")
endif ()
if (NOT "${freetype_EXE_LINK_FLAGS_RELEASE}" STREQUAL "")
    list(APPEND freetype_LINKER_FLAGS_RELEASE
        "$<$<STREQUAL:$<TARGET_PROPERTY:TYPE>,EXECUTABLE>:${freetype_EXE_LINK_FLAGS_RELEASE}>")
endif ()


set(freetype_COMPONENTS_RELEASE )