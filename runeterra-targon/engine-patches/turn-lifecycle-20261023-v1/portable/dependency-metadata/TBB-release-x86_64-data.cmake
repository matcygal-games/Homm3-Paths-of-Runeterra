########### AGGREGATED COMPONENTS AND DEPENDENCIES FOR THE MULTI CONFIG #####################
#############################################################################################

list(APPEND onetbb_COMPONENT_NAMES TBB::tbb)
list(REMOVE_DUPLICATES onetbb_COMPONENT_NAMES)
if(DEFINED onetbb_FIND_DEPENDENCY_NAMES)
  list(APPEND onetbb_FIND_DEPENDENCY_NAMES )
  list(REMOVE_DUPLICATES onetbb_FIND_DEPENDENCY_NAMES)
else()
  set(onetbb_FIND_DEPENDENCY_NAMES )
endif()

########### VARIABLES #######################################################################
#############################################################################################
set(onetbb_PACKAGE_FOLDER_RELEASE "<SDK_ROOT>/conan-home/p/onetbeec24a0b9e43d/p")
set(onetbb_BUILD_MODULES_PATHS_RELEASE )


set(onetbb_INCLUDE_DIRS_RELEASE "${onetbb_PACKAGE_FOLDER_RELEASE}/include")
set(onetbb_RES_DIRS_RELEASE )
set(onetbb_DEFINITIONS_RELEASE )
set(onetbb_SHARED_LINK_FLAGS_RELEASE )
set(onetbb_EXE_LINK_FLAGS_RELEASE )
set(onetbb_OBJECTS_RELEASE )
set(onetbb_COMPILE_DEFINITIONS_RELEASE )
set(onetbb_COMPILE_OPTIONS_C_RELEASE )
set(onetbb_COMPILE_OPTIONS_CXX_RELEASE )
set(onetbb_LIB_DIRS_RELEASE "${onetbb_PACKAGE_FOLDER_RELEASE}/lib")
set(onetbb_BIN_DIRS_RELEASE "${onetbb_PACKAGE_FOLDER_RELEASE}/bin")
set(onetbb_LIBRARY_TYPE_RELEASE SHARED)
set(onetbb_IS_HOST_WINDOWS_RELEASE 1)
set(onetbb_LIBS_RELEASE tbb tbb12)
set(onetbb_SYSTEM_LIBS_RELEASE )
set(onetbb_FRAMEWORK_DIRS_RELEASE )
set(onetbb_FRAMEWORKS_RELEASE )
set(onetbb_BUILD_DIRS_RELEASE )
set(onetbb_NO_SONAME_MODE_RELEASE FALSE)


# COMPOUND VARIABLES
set(onetbb_COMPILE_OPTIONS_RELEASE)
if (NOT "${onetbb_COMPILE_OPTIONS_CXX_RELEASE}" STREQUAL "")
    list(APPEND onetbb_COMPILE_OPTIONS_RELEASE
        "$<$<COMPILE_LANGUAGE:CXX>:${onetbb_COMPILE_OPTIONS_CXX_RELEASE}>")
endif ()
if (NOT "${onetbb_COMPILE_OPTIONS_C_RELEASE}" STREQUAL "")
    list(APPEND onetbb_COMPILE_OPTIONS_RELEASE
        "$<$<COMPILE_LANGUAGE:C>:${onetbb_COMPILE_OPTIONS_C_RELEASE}>")
endif ()
set(onetbb_LINKER_FLAGS_RELEASE)
if (NOT "${onetbb_SHARED_LINK_FLAGS_RELEASE}" STREQUAL "")
    list(APPEND onetbb_LINKER_FLAGS_RELEASE
        "$<$<OR:$<STREQUAL:$<TARGET_PROPERTY:TYPE>,SHARED_LIBRARY>,$<STREQUAL:$<TARGET_PROPERTY:TYPE>,MODULE_LIBRARY>>:${onetbb_SHARED_LINK_FLAGS_RELEASE}>")
endif ()
if (NOT "${onetbb_EXE_LINK_FLAGS_RELEASE}" STREQUAL "")
    list(APPEND onetbb_LINKER_FLAGS_RELEASE
        "$<$<STREQUAL:$<TARGET_PROPERTY:TYPE>,EXECUTABLE>:${onetbb_EXE_LINK_FLAGS_RELEASE}>")
endif ()


set(onetbb_COMPONENTS_RELEASE TBB::tbb)
########### COMPONENT TBB::tbb VARIABLES ############################################

set(onetbb_TBB_tbb_INCLUDE_DIRS_RELEASE "${onetbb_PACKAGE_FOLDER_RELEASE}/include")
set(onetbb_TBB_tbb_LIB_DIRS_RELEASE "${onetbb_PACKAGE_FOLDER_RELEASE}/lib")
set(onetbb_TBB_tbb_BIN_DIRS_RELEASE "${onetbb_PACKAGE_FOLDER_RELEASE}/bin")
set(onetbb_TBB_tbb_LIBRARY_TYPE_RELEASE SHARED)
set(onetbb_TBB_tbb_IS_HOST_WINDOWS_RELEASE 1)
set(onetbb_TBB_tbb_RES_DIRS_RELEASE )
set(onetbb_TBB_tbb_DEFINITIONS_RELEASE )
set(onetbb_TBB_tbb_OBJECTS_RELEASE )
set(onetbb_TBB_tbb_COMPILE_DEFINITIONS_RELEASE )
set(onetbb_TBB_tbb_COMPILE_OPTIONS_C_RELEASE "")
set(onetbb_TBB_tbb_COMPILE_OPTIONS_CXX_RELEASE "")
set(onetbb_TBB_tbb_LIBS_RELEASE tbb tbb12)
set(onetbb_TBB_tbb_SYSTEM_LIBS_RELEASE )
set(onetbb_TBB_tbb_FRAMEWORK_DIRS_RELEASE )
set(onetbb_TBB_tbb_FRAMEWORKS_RELEASE )
set(onetbb_TBB_tbb_DEPENDENCIES_RELEASE )
set(onetbb_TBB_tbb_SHARED_LINK_FLAGS_RELEASE )
set(onetbb_TBB_tbb_EXE_LINK_FLAGS_RELEASE )
set(onetbb_TBB_tbb_NO_SONAME_MODE_RELEASE FALSE)

# COMPOUND VARIABLES
set(onetbb_TBB_tbb_LINKER_FLAGS_RELEASE)
if (NOT "${onetbb_TBB_tbb_SHARED_LINK_FLAGS_RELEASE}" STREQUAL "")
    list(APPEND onetbb_TBB_tbb_LINKER_FLAGS_RELEASE
        $<$<OR:$<STREQUAL:$<TARGET_PROPERTY:TYPE>,SHARED_LIBRARY>,$<STREQUAL:$<TARGET_PROPERTY:TYPE>,MODULE_LIBRARY>>:${onetbb_TBB_tbb_SHARED_LINK_FLAGS_RELEASE}>)
endif ()
if (NOT "${onetbb_TBB_tbb_EXE_LINK_FLAGS_RELEASE}" STREQUAL "")
    list(APPEND onetbb_TBB_tbb_LINKER_FLAGS_RELEASE
        $<$<STREQUAL:$<TARGET_PROPERTY:TYPE>,EXECUTABLE>:${onetbb_TBB_tbb_EXE_LINK_FLAGS_RELEASE}>)
endif ()
set(onetbb_TBB_tbb_COMPILE_OPTIONS_RELEASE)
if (NOT "${onetbb_TBB_tbb_COMPILE_OPTIONS_CXX_RELEASE}" STREQUAL "")
    list(APPEND onetbb_TBB_tbb_COMPILE_OPTIONS_RELEASE
        "$<$<COMPILE_LANGUAGE:CXX>:${onetbb_TBB_tbb_COMPILE_OPTIONS_CXX_RELEASE}>")
endif ()
if (NOT "${onetbb_TBB_tbb_COMPILE_OPTIONS_C_RELEASE}" STREQUAL "")
    list(APPEND onetbb_TBB_tbb_COMPILE_OPTIONS_RELEASE
        "$<$<COMPILE_LANGUAGE:C>:${onetbb_TBB_tbb_COMPILE_OPTIONS_C_RELEASE}>")
endif ()