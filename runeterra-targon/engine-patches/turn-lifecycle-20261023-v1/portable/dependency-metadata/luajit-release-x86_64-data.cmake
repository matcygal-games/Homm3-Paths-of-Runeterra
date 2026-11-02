########### AGGREGATED COMPONENTS AND DEPENDENCIES FOR THE MULTI CONFIG #####################
#############################################################################################

set(luajit_COMPONENT_NAMES "")
if(DEFINED luajit_FIND_DEPENDENCY_NAMES)
  list(APPEND luajit_FIND_DEPENDENCY_NAMES )
  list(REMOVE_DUPLICATES luajit_FIND_DEPENDENCY_NAMES)
else()
  set(luajit_FIND_DEPENDENCY_NAMES )
endif()

########### VARIABLES #######################################################################
#############################################################################################
set(luajit_PACKAGE_FOLDER_RELEASE "<SDK_ROOT>/conan-home/p/luajicb3d27f823ff2/p")
set(luajit_BUILD_MODULES_PATHS_RELEASE )


set(luajit_INCLUDE_DIRS_RELEASE "${luajit_PACKAGE_FOLDER_RELEASE}/include/luajit-2.1")
set(luajit_RES_DIRS_RELEASE )
set(luajit_DEFINITIONS_RELEASE )
set(luajit_SHARED_LINK_FLAGS_RELEASE )
set(luajit_EXE_LINK_FLAGS_RELEASE )
set(luajit_OBJECTS_RELEASE )
set(luajit_COMPILE_DEFINITIONS_RELEASE )
set(luajit_COMPILE_OPTIONS_C_RELEASE )
set(luajit_COMPILE_OPTIONS_CXX_RELEASE )
set(luajit_LIB_DIRS_RELEASE "${luajit_PACKAGE_FOLDER_RELEASE}/lib")
set(luajit_BIN_DIRS_RELEASE )
set(luajit_LIBRARY_TYPE_RELEASE STATIC)
set(luajit_IS_HOST_WINDOWS_RELEASE 1)
set(luajit_LIBS_RELEASE lua51)
set(luajit_SYSTEM_LIBS_RELEASE )
set(luajit_FRAMEWORK_DIRS_RELEASE )
set(luajit_FRAMEWORKS_RELEASE )
set(luajit_BUILD_DIRS_RELEASE )
set(luajit_NO_SONAME_MODE_RELEASE FALSE)


# COMPOUND VARIABLES
set(luajit_COMPILE_OPTIONS_RELEASE)
if (NOT "${luajit_COMPILE_OPTIONS_CXX_RELEASE}" STREQUAL "")
    list(APPEND luajit_COMPILE_OPTIONS_RELEASE
        "$<$<COMPILE_LANGUAGE:CXX>:${luajit_COMPILE_OPTIONS_CXX_RELEASE}>")
endif ()
if (NOT "${luajit_COMPILE_OPTIONS_C_RELEASE}" STREQUAL "")
    list(APPEND luajit_COMPILE_OPTIONS_RELEASE
        "$<$<COMPILE_LANGUAGE:C>:${luajit_COMPILE_OPTIONS_C_RELEASE}>")
endif ()
set(luajit_LINKER_FLAGS_RELEASE)
if (NOT "${luajit_SHARED_LINK_FLAGS_RELEASE}" STREQUAL "")
    list(APPEND luajit_LINKER_FLAGS_RELEASE
        "$<$<OR:$<STREQUAL:$<TARGET_PROPERTY:TYPE>,SHARED_LIBRARY>,$<STREQUAL:$<TARGET_PROPERTY:TYPE>,MODULE_LIBRARY>>:${luajit_SHARED_LINK_FLAGS_RELEASE}>")
endif ()
if (NOT "${luajit_EXE_LINK_FLAGS_RELEASE}" STREQUAL "")
    list(APPEND luajit_LINKER_FLAGS_RELEASE
        "$<$<STREQUAL:$<TARGET_PROPERTY:TYPE>,EXECUTABLE>:${luajit_EXE_LINK_FLAGS_RELEASE}>")
endif ()


set(luajit_COMPONENTS_RELEASE )