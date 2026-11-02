########### AGGREGATED COMPONENTS AND DEPENDENCIES FOR THE MULTI CONFIG #####################
#############################################################################################

list(APPEND libcurl_COMPONENT_NAMES CURL::libcurl)
list(REMOVE_DUPLICATES libcurl_COMPONENT_NAMES)
if(DEFINED libcurl_FIND_DEPENDENCY_NAMES)
  list(APPEND libcurl_FIND_DEPENDENCY_NAMES ZLIB)
  list(REMOVE_DUPLICATES libcurl_FIND_DEPENDENCY_NAMES)
else()
  set(libcurl_FIND_DEPENDENCY_NAMES ZLIB)
endif()
set(ZLIB_FIND_MODE "MODULE")

########### VARIABLES #######################################################################
#############################################################################################
set(libcurl_PACKAGE_FOLDER_RELEASE "<SDK_ROOT>/conan-home/p/libcu421ab03bf8dff/p")
set(libcurl_BUILD_MODULES_PATHS_RELEASE )


set(libcurl_INCLUDE_DIRS_RELEASE "${libcurl_PACKAGE_FOLDER_RELEASE}/include")
set(libcurl_RES_DIRS_RELEASE "${libcurl_PACKAGE_FOLDER_RELEASE}/res")
set(libcurl_DEFINITIONS_RELEASE "-DCURL_STATICLIB=1")
set(libcurl_SHARED_LINK_FLAGS_RELEASE )
set(libcurl_EXE_LINK_FLAGS_RELEASE )
set(libcurl_OBJECTS_RELEASE )
set(libcurl_COMPILE_DEFINITIONS_RELEASE "CURL_STATICLIB=1")
set(libcurl_COMPILE_OPTIONS_C_RELEASE )
set(libcurl_COMPILE_OPTIONS_CXX_RELEASE )
set(libcurl_LIB_DIRS_RELEASE "${libcurl_PACKAGE_FOLDER_RELEASE}/lib")
set(libcurl_BIN_DIRS_RELEASE )
set(libcurl_LIBRARY_TYPE_RELEASE STATIC)
set(libcurl_IS_HOST_WINDOWS_RELEASE 1)
set(libcurl_LIBS_RELEASE libcurl)
set(libcurl_SYSTEM_LIBS_RELEASE ws2_32 bcrypt iphlpapi crypt32 secur32)
set(libcurl_FRAMEWORK_DIRS_RELEASE )
set(libcurl_FRAMEWORKS_RELEASE )
set(libcurl_BUILD_DIRS_RELEASE )
set(libcurl_NO_SONAME_MODE_RELEASE FALSE)


# COMPOUND VARIABLES
set(libcurl_COMPILE_OPTIONS_RELEASE)
if (NOT "${libcurl_COMPILE_OPTIONS_CXX_RELEASE}" STREQUAL "")
    list(APPEND libcurl_COMPILE_OPTIONS_RELEASE
        "$<$<COMPILE_LANGUAGE:CXX>:${libcurl_COMPILE_OPTIONS_CXX_RELEASE}>")
endif ()
if (NOT "${libcurl_COMPILE_OPTIONS_C_RELEASE}" STREQUAL "")
    list(APPEND libcurl_COMPILE_OPTIONS_RELEASE
        "$<$<COMPILE_LANGUAGE:C>:${libcurl_COMPILE_OPTIONS_C_RELEASE}>")
endif ()
set(libcurl_LINKER_FLAGS_RELEASE)
if (NOT "${libcurl_SHARED_LINK_FLAGS_RELEASE}" STREQUAL "")
    list(APPEND libcurl_LINKER_FLAGS_RELEASE
        "$<$<OR:$<STREQUAL:$<TARGET_PROPERTY:TYPE>,SHARED_LIBRARY>,$<STREQUAL:$<TARGET_PROPERTY:TYPE>,MODULE_LIBRARY>>:${libcurl_SHARED_LINK_FLAGS_RELEASE}>")
endif ()
if (NOT "${libcurl_EXE_LINK_FLAGS_RELEASE}" STREQUAL "")
    list(APPEND libcurl_LINKER_FLAGS_RELEASE
        "$<$<STREQUAL:$<TARGET_PROPERTY:TYPE>,EXECUTABLE>:${libcurl_EXE_LINK_FLAGS_RELEASE}>")
endif ()


set(libcurl_COMPONENTS_RELEASE CURL::libcurl)
########### COMPONENT CURL::libcurl VARIABLES ############################################

set(libcurl_CURL_libcurl_INCLUDE_DIRS_RELEASE "${libcurl_PACKAGE_FOLDER_RELEASE}/include")
set(libcurl_CURL_libcurl_LIB_DIRS_RELEASE "${libcurl_PACKAGE_FOLDER_RELEASE}/lib")
set(libcurl_CURL_libcurl_BIN_DIRS_RELEASE )
set(libcurl_CURL_libcurl_LIBRARY_TYPE_RELEASE STATIC)
set(libcurl_CURL_libcurl_IS_HOST_WINDOWS_RELEASE 1)
set(libcurl_CURL_libcurl_RES_DIRS_RELEASE "${libcurl_PACKAGE_FOLDER_RELEASE}/res")
set(libcurl_CURL_libcurl_DEFINITIONS_RELEASE "-DCURL_STATICLIB=1")
set(libcurl_CURL_libcurl_OBJECTS_RELEASE )
set(libcurl_CURL_libcurl_COMPILE_DEFINITIONS_RELEASE "CURL_STATICLIB=1")
set(libcurl_CURL_libcurl_COMPILE_OPTIONS_C_RELEASE "")
set(libcurl_CURL_libcurl_COMPILE_OPTIONS_CXX_RELEASE "")
set(libcurl_CURL_libcurl_LIBS_RELEASE libcurl)
set(libcurl_CURL_libcurl_SYSTEM_LIBS_RELEASE ws2_32 bcrypt iphlpapi crypt32 secur32)
set(libcurl_CURL_libcurl_FRAMEWORK_DIRS_RELEASE )
set(libcurl_CURL_libcurl_FRAMEWORKS_RELEASE )
set(libcurl_CURL_libcurl_DEPENDENCIES_RELEASE ZLIB::ZLIB)
set(libcurl_CURL_libcurl_SHARED_LINK_FLAGS_RELEASE )
set(libcurl_CURL_libcurl_EXE_LINK_FLAGS_RELEASE )
set(libcurl_CURL_libcurl_NO_SONAME_MODE_RELEASE FALSE)

# COMPOUND VARIABLES
set(libcurl_CURL_libcurl_LINKER_FLAGS_RELEASE)
if (NOT "${libcurl_CURL_libcurl_SHARED_LINK_FLAGS_RELEASE}" STREQUAL "")
    list(APPEND libcurl_CURL_libcurl_LINKER_FLAGS_RELEASE
        $<$<OR:$<STREQUAL:$<TARGET_PROPERTY:TYPE>,SHARED_LIBRARY>,$<STREQUAL:$<TARGET_PROPERTY:TYPE>,MODULE_LIBRARY>>:${libcurl_CURL_libcurl_SHARED_LINK_FLAGS_RELEASE}>)
endif ()
if (NOT "${libcurl_CURL_libcurl_EXE_LINK_FLAGS_RELEASE}" STREQUAL "")
    list(APPEND libcurl_CURL_libcurl_LINKER_FLAGS_RELEASE
        $<$<STREQUAL:$<TARGET_PROPERTY:TYPE>,EXECUTABLE>:${libcurl_CURL_libcurl_EXE_LINK_FLAGS_RELEASE}>)
endif ()
set(libcurl_CURL_libcurl_COMPILE_OPTIONS_RELEASE)
if (NOT "${libcurl_CURL_libcurl_COMPILE_OPTIONS_CXX_RELEASE}" STREQUAL "")
    list(APPEND libcurl_CURL_libcurl_COMPILE_OPTIONS_RELEASE
        "$<$<COMPILE_LANGUAGE:CXX>:${libcurl_CURL_libcurl_COMPILE_OPTIONS_CXX_RELEASE}>")
endif ()
if (NOT "${libcurl_CURL_libcurl_COMPILE_OPTIONS_C_RELEASE}" STREQUAL "")
    list(APPEND libcurl_CURL_libcurl_COMPILE_OPTIONS_RELEASE
        "$<$<COMPILE_LANGUAGE:C>:${libcurl_CURL_libcurl_COMPILE_OPTIONS_C_RELEASE}>")
endif ()