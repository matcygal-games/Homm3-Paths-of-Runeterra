########### AGGREGATED COMPONENTS AND DEPENDENCIES FOR THE MULTI CONFIG #####################
#############################################################################################

list(APPEND opus_COMPONENT_NAMES Opus::opus)
list(REMOVE_DUPLICATES opus_COMPONENT_NAMES)
if(DEFINED opus_FIND_DEPENDENCY_NAMES)
  list(APPEND opus_FIND_DEPENDENCY_NAMES )
  list(REMOVE_DUPLICATES opus_FIND_DEPENDENCY_NAMES)
else()
  set(opus_FIND_DEPENDENCY_NAMES )
endif()

########### VARIABLES #######################################################################
#############################################################################################
set(opus_PACKAGE_FOLDER_RELEASE "<SDK_ROOT>/conan-home/p/opusa6deb694451ce/p")
set(opus_BUILD_MODULES_PATHS_RELEASE )


set(opus_INCLUDE_DIRS_RELEASE "${opus_PACKAGE_FOLDER_RELEASE}/include"
			"${opus_PACKAGE_FOLDER_RELEASE}/include/opus")
set(opus_RES_DIRS_RELEASE )
set(opus_DEFINITIONS_RELEASE )
set(opus_SHARED_LINK_FLAGS_RELEASE )
set(opus_EXE_LINK_FLAGS_RELEASE )
set(opus_OBJECTS_RELEASE )
set(opus_COMPILE_DEFINITIONS_RELEASE )
set(opus_COMPILE_OPTIONS_C_RELEASE )
set(opus_COMPILE_OPTIONS_CXX_RELEASE )
set(opus_LIB_DIRS_RELEASE "${opus_PACKAGE_FOLDER_RELEASE}/lib")
set(opus_BIN_DIRS_RELEASE "${opus_PACKAGE_FOLDER_RELEASE}/bin")
set(opus_LIBRARY_TYPE_RELEASE SHARED)
set(opus_IS_HOST_WINDOWS_RELEASE 1)
set(opus_LIBS_RELEASE opus)
set(opus_SYSTEM_LIBS_RELEASE )
set(opus_FRAMEWORK_DIRS_RELEASE )
set(opus_FRAMEWORKS_RELEASE )
set(opus_BUILD_DIRS_RELEASE )
set(opus_NO_SONAME_MODE_RELEASE FALSE)


# COMPOUND VARIABLES
set(opus_COMPILE_OPTIONS_RELEASE)
if (NOT "${opus_COMPILE_OPTIONS_CXX_RELEASE}" STREQUAL "")
    list(APPEND opus_COMPILE_OPTIONS_RELEASE
        "$<$<COMPILE_LANGUAGE:CXX>:${opus_COMPILE_OPTIONS_CXX_RELEASE}>")
endif ()
if (NOT "${opus_COMPILE_OPTIONS_C_RELEASE}" STREQUAL "")
    list(APPEND opus_COMPILE_OPTIONS_RELEASE
        "$<$<COMPILE_LANGUAGE:C>:${opus_COMPILE_OPTIONS_C_RELEASE}>")
endif ()
set(opus_LINKER_FLAGS_RELEASE)
if (NOT "${opus_SHARED_LINK_FLAGS_RELEASE}" STREQUAL "")
    list(APPEND opus_LINKER_FLAGS_RELEASE
        "$<$<OR:$<STREQUAL:$<TARGET_PROPERTY:TYPE>,SHARED_LIBRARY>,$<STREQUAL:$<TARGET_PROPERTY:TYPE>,MODULE_LIBRARY>>:${opus_SHARED_LINK_FLAGS_RELEASE}>")
endif ()
if (NOT "${opus_EXE_LINK_FLAGS_RELEASE}" STREQUAL "")
    list(APPEND opus_LINKER_FLAGS_RELEASE
        "$<$<STREQUAL:$<TARGET_PROPERTY:TYPE>,EXECUTABLE>:${opus_EXE_LINK_FLAGS_RELEASE}>")
endif ()


set(opus_COMPONENTS_RELEASE Opus::opus)
########### COMPONENT Opus::opus VARIABLES ############################################

set(opus_Opus_opus_INCLUDE_DIRS_RELEASE "${opus_PACKAGE_FOLDER_RELEASE}/include"
			"${opus_PACKAGE_FOLDER_RELEASE}/include/opus")
set(opus_Opus_opus_LIB_DIRS_RELEASE "${opus_PACKAGE_FOLDER_RELEASE}/lib")
set(opus_Opus_opus_BIN_DIRS_RELEASE "${opus_PACKAGE_FOLDER_RELEASE}/bin")
set(opus_Opus_opus_LIBRARY_TYPE_RELEASE SHARED)
set(opus_Opus_opus_IS_HOST_WINDOWS_RELEASE 1)
set(opus_Opus_opus_RES_DIRS_RELEASE )
set(opus_Opus_opus_DEFINITIONS_RELEASE )
set(opus_Opus_opus_OBJECTS_RELEASE )
set(opus_Opus_opus_COMPILE_DEFINITIONS_RELEASE )
set(opus_Opus_opus_COMPILE_OPTIONS_C_RELEASE "")
set(opus_Opus_opus_COMPILE_OPTIONS_CXX_RELEASE "")
set(opus_Opus_opus_LIBS_RELEASE opus)
set(opus_Opus_opus_SYSTEM_LIBS_RELEASE )
set(opus_Opus_opus_FRAMEWORK_DIRS_RELEASE )
set(opus_Opus_opus_FRAMEWORKS_RELEASE )
set(opus_Opus_opus_DEPENDENCIES_RELEASE )
set(opus_Opus_opus_SHARED_LINK_FLAGS_RELEASE )
set(opus_Opus_opus_EXE_LINK_FLAGS_RELEASE )
set(opus_Opus_opus_NO_SONAME_MODE_RELEASE FALSE)

# COMPOUND VARIABLES
set(opus_Opus_opus_LINKER_FLAGS_RELEASE)
if (NOT "${opus_Opus_opus_SHARED_LINK_FLAGS_RELEASE}" STREQUAL "")
    list(APPEND opus_Opus_opus_LINKER_FLAGS_RELEASE
        $<$<OR:$<STREQUAL:$<TARGET_PROPERTY:TYPE>,SHARED_LIBRARY>,$<STREQUAL:$<TARGET_PROPERTY:TYPE>,MODULE_LIBRARY>>:${opus_Opus_opus_SHARED_LINK_FLAGS_RELEASE}>)
endif ()
if (NOT "${opus_Opus_opus_EXE_LINK_FLAGS_RELEASE}" STREQUAL "")
    list(APPEND opus_Opus_opus_LINKER_FLAGS_RELEASE
        $<$<STREQUAL:$<TARGET_PROPERTY:TYPE>,EXECUTABLE>:${opus_Opus_opus_EXE_LINK_FLAGS_RELEASE}>)
endif ()
set(opus_Opus_opus_COMPILE_OPTIONS_RELEASE)
if (NOT "${opus_Opus_opus_COMPILE_OPTIONS_CXX_RELEASE}" STREQUAL "")
    list(APPEND opus_Opus_opus_COMPILE_OPTIONS_RELEASE
        "$<$<COMPILE_LANGUAGE:CXX>:${opus_Opus_opus_COMPILE_OPTIONS_CXX_RELEASE}>")
endif ()
if (NOT "${opus_Opus_opus_COMPILE_OPTIONS_C_RELEASE}" STREQUAL "")
    list(APPEND opus_Opus_opus_COMPILE_OPTIONS_RELEASE
        "$<$<COMPILE_LANGUAGE:C>:${opus_Opus_opus_COMPILE_OPTIONS_C_RELEASE}>")
endif ()