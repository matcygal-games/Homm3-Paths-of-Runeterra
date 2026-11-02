########### AGGREGATED COMPONENTS AND DEPENDENCIES FOR THE MULTI CONFIG #####################
#############################################################################################

list(APPEND boost_COMPONENT_NAMES Boost::diagnostic_definitions Boost::disable_autolinking Boost::dynamic_linking boost::process Boost::headers Boost::boost boost::_libboost Boost::atomic Boost::date_time Boost::program_options Boost::regex Boost::system Boost::filesystem Boost::random Boost::iostreams)
list(REMOVE_DUPLICATES boost_COMPONENT_NAMES)
if(DEFINED boost_FIND_DEPENDENCY_NAMES)
  list(APPEND boost_FIND_DEPENDENCY_NAMES BZip2 ZLIB)
  list(REMOVE_DUPLICATES boost_FIND_DEPENDENCY_NAMES)
else()
  set(boost_FIND_DEPENDENCY_NAMES BZip2 ZLIB)
endif()
set(BZip2_FIND_MODE "NO_MODULE")
set(ZLIB_FIND_MODE "NO_MODULE")

########### VARIABLES #######################################################################
#############################################################################################
set(boost_PACKAGE_FOLDER_RELEASE "<SDK_ROOT>/conan-home/p/boost2daea649742b4/p")
set(boost_BUILD_MODULES_PATHS_RELEASE )


set(boost_INCLUDE_DIRS_RELEASE "${boost_PACKAGE_FOLDER_RELEASE}/include")
set(boost_RES_DIRS_RELEASE )
set(boost_DEFINITIONS_RELEASE "-DBOOST_PROCESS_DYN_LINK"
			"-DBOOST_ALL_DYN_LINK"
			"-DBOOST_ALL_NO_LIB")
set(boost_SHARED_LINK_FLAGS_RELEASE )
set(boost_EXE_LINK_FLAGS_RELEASE )
set(boost_OBJECTS_RELEASE )
set(boost_COMPILE_DEFINITIONS_RELEASE "BOOST_PROCESS_DYN_LINK"
			"BOOST_ALL_DYN_LINK"
			"BOOST_ALL_NO_LIB")
set(boost_COMPILE_OPTIONS_C_RELEASE )
set(boost_COMPILE_OPTIONS_CXX_RELEASE )
set(boost_LIB_DIRS_RELEASE "${boost_PACKAGE_FOLDER_RELEASE}/lib")
set(boost_BIN_DIRS_RELEASE "${boost_PACKAGE_FOLDER_RELEASE}/bin")
set(boost_LIBRARY_TYPE_RELEASE SHARED)
set(boost_IS_HOST_WINDOWS_RELEASE 1)
set(boost_LIBS_RELEASE boost_iostreams boost_random boost_filesystem boost_regex boost_program_options boost_date_time boost_atomic)
set(boost_SYSTEM_LIBS_RELEASE bcrypt ntdll shell32 advapi32 user32)
set(boost_FRAMEWORK_DIRS_RELEASE )
set(boost_FRAMEWORKS_RELEASE )
set(boost_BUILD_DIRS_RELEASE )
set(boost_NO_SONAME_MODE_RELEASE FALSE)


# COMPOUND VARIABLES
set(boost_COMPILE_OPTIONS_RELEASE)
if (NOT "${boost_COMPILE_OPTIONS_CXX_RELEASE}" STREQUAL "")
    list(APPEND boost_COMPILE_OPTIONS_RELEASE
        "$<$<COMPILE_LANGUAGE:CXX>:${boost_COMPILE_OPTIONS_CXX_RELEASE}>")
endif ()
if (NOT "${boost_COMPILE_OPTIONS_C_RELEASE}" STREQUAL "")
    list(APPEND boost_COMPILE_OPTIONS_RELEASE
        "$<$<COMPILE_LANGUAGE:C>:${boost_COMPILE_OPTIONS_C_RELEASE}>")
endif ()
set(boost_LINKER_FLAGS_RELEASE)
if (NOT "${boost_SHARED_LINK_FLAGS_RELEASE}" STREQUAL "")
    list(APPEND boost_LINKER_FLAGS_RELEASE
        "$<$<OR:$<STREQUAL:$<TARGET_PROPERTY:TYPE>,SHARED_LIBRARY>,$<STREQUAL:$<TARGET_PROPERTY:TYPE>,MODULE_LIBRARY>>:${boost_SHARED_LINK_FLAGS_RELEASE}>")
endif ()
if (NOT "${boost_EXE_LINK_FLAGS_RELEASE}" STREQUAL "")
    list(APPEND boost_LINKER_FLAGS_RELEASE
        "$<$<STREQUAL:$<TARGET_PROPERTY:TYPE>,EXECUTABLE>:${boost_EXE_LINK_FLAGS_RELEASE}>")
endif ()


set(boost_COMPONENTS_RELEASE Boost::diagnostic_definitions Boost::disable_autolinking Boost::dynamic_linking boost::process Boost::headers Boost::boost boost::_libboost Boost::atomic Boost::date_time Boost::program_options Boost::regex Boost::system Boost::filesystem Boost::random Boost::iostreams)
########### COMPONENT Boost::iostreams VARIABLES ############################################

set(boost_Boost_iostreams_INCLUDE_DIRS_RELEASE "${boost_PACKAGE_FOLDER_RELEASE}/include")
set(boost_Boost_iostreams_LIB_DIRS_RELEASE "${boost_PACKAGE_FOLDER_RELEASE}/lib")
set(boost_Boost_iostreams_BIN_DIRS_RELEASE "${boost_PACKAGE_FOLDER_RELEASE}/bin")
set(boost_Boost_iostreams_LIBRARY_TYPE_RELEASE SHARED)
set(boost_Boost_iostreams_IS_HOST_WINDOWS_RELEASE 1)
set(boost_Boost_iostreams_RES_DIRS_RELEASE )
set(boost_Boost_iostreams_DEFINITIONS_RELEASE )
set(boost_Boost_iostreams_OBJECTS_RELEASE )
set(boost_Boost_iostreams_COMPILE_DEFINITIONS_RELEASE )
set(boost_Boost_iostreams_COMPILE_OPTIONS_C_RELEASE "")
set(boost_Boost_iostreams_COMPILE_OPTIONS_CXX_RELEASE "")
set(boost_Boost_iostreams_LIBS_RELEASE boost_iostreams)
set(boost_Boost_iostreams_SYSTEM_LIBS_RELEASE )
set(boost_Boost_iostreams_FRAMEWORK_DIRS_RELEASE )
set(boost_Boost_iostreams_FRAMEWORKS_RELEASE )
set(boost_Boost_iostreams_DEPENDENCIES_RELEASE Boost::random Boost::regex boost::_libboost BZip2::BZip2 ZLIB::ZLIB)
set(boost_Boost_iostreams_SHARED_LINK_FLAGS_RELEASE )
set(boost_Boost_iostreams_EXE_LINK_FLAGS_RELEASE )
set(boost_Boost_iostreams_NO_SONAME_MODE_RELEASE FALSE)

# COMPOUND VARIABLES
set(boost_Boost_iostreams_LINKER_FLAGS_RELEASE)
if (NOT "${boost_Boost_iostreams_SHARED_LINK_FLAGS_RELEASE}" STREQUAL "")
    list(APPEND boost_Boost_iostreams_LINKER_FLAGS_RELEASE
        $<$<OR:$<STREQUAL:$<TARGET_PROPERTY:TYPE>,SHARED_LIBRARY>,$<STREQUAL:$<TARGET_PROPERTY:TYPE>,MODULE_LIBRARY>>:${boost_Boost_iostreams_SHARED_LINK_FLAGS_RELEASE}>)
endif ()
if (NOT "${boost_Boost_iostreams_EXE_LINK_FLAGS_RELEASE}" STREQUAL "")
    list(APPEND boost_Boost_iostreams_LINKER_FLAGS_RELEASE
        $<$<STREQUAL:$<TARGET_PROPERTY:TYPE>,EXECUTABLE>:${boost_Boost_iostreams_EXE_LINK_FLAGS_RELEASE}>)
endif ()
set(boost_Boost_iostreams_COMPILE_OPTIONS_RELEASE)
if (NOT "${boost_Boost_iostreams_COMPILE_OPTIONS_CXX_RELEASE}" STREQUAL "")
    list(APPEND boost_Boost_iostreams_COMPILE_OPTIONS_RELEASE
        "$<$<COMPILE_LANGUAGE:CXX>:${boost_Boost_iostreams_COMPILE_OPTIONS_CXX_RELEASE}>")
endif ()
if (NOT "${boost_Boost_iostreams_COMPILE_OPTIONS_C_RELEASE}" STREQUAL "")
    list(APPEND boost_Boost_iostreams_COMPILE_OPTIONS_RELEASE
        "$<$<COMPILE_LANGUAGE:C>:${boost_Boost_iostreams_COMPILE_OPTIONS_C_RELEASE}>")
endif ()
########### COMPONENT Boost::random VARIABLES ############################################

set(boost_Boost_random_INCLUDE_DIRS_RELEASE "${boost_PACKAGE_FOLDER_RELEASE}/include")
set(boost_Boost_random_LIB_DIRS_RELEASE "${boost_PACKAGE_FOLDER_RELEASE}/lib")
set(boost_Boost_random_BIN_DIRS_RELEASE "${boost_PACKAGE_FOLDER_RELEASE}/bin")
set(boost_Boost_random_LIBRARY_TYPE_RELEASE SHARED)
set(boost_Boost_random_IS_HOST_WINDOWS_RELEASE 1)
set(boost_Boost_random_RES_DIRS_RELEASE )
set(boost_Boost_random_DEFINITIONS_RELEASE )
set(boost_Boost_random_OBJECTS_RELEASE )
set(boost_Boost_random_COMPILE_DEFINITIONS_RELEASE )
set(boost_Boost_random_COMPILE_OPTIONS_C_RELEASE "")
set(boost_Boost_random_COMPILE_OPTIONS_CXX_RELEASE "")
set(boost_Boost_random_LIBS_RELEASE boost_random)
set(boost_Boost_random_SYSTEM_LIBS_RELEASE )
set(boost_Boost_random_FRAMEWORK_DIRS_RELEASE )
set(boost_Boost_random_FRAMEWORKS_RELEASE )
set(boost_Boost_random_DEPENDENCIES_RELEASE Boost::system boost::_libboost)
set(boost_Boost_random_SHARED_LINK_FLAGS_RELEASE )
set(boost_Boost_random_EXE_LINK_FLAGS_RELEASE )
set(boost_Boost_random_NO_SONAME_MODE_RELEASE FALSE)

# COMPOUND VARIABLES
set(boost_Boost_random_LINKER_FLAGS_RELEASE)
if (NOT "${boost_Boost_random_SHARED_LINK_FLAGS_RELEASE}" STREQUAL "")
    list(APPEND boost_Boost_random_LINKER_FLAGS_RELEASE
        $<$<OR:$<STREQUAL:$<TARGET_PROPERTY:TYPE>,SHARED_LIBRARY>,$<STREQUAL:$<TARGET_PROPERTY:TYPE>,MODULE_LIBRARY>>:${boost_Boost_random_SHARED_LINK_FLAGS_RELEASE}>)
endif ()
if (NOT "${boost_Boost_random_EXE_LINK_FLAGS_RELEASE}" STREQUAL "")
    list(APPEND boost_Boost_random_LINKER_FLAGS_RELEASE
        $<$<STREQUAL:$<TARGET_PROPERTY:TYPE>,EXECUTABLE>:${boost_Boost_random_EXE_LINK_FLAGS_RELEASE}>)
endif ()
set(boost_Boost_random_COMPILE_OPTIONS_RELEASE)
if (NOT "${boost_Boost_random_COMPILE_OPTIONS_CXX_RELEASE}" STREQUAL "")
    list(APPEND boost_Boost_random_COMPILE_OPTIONS_RELEASE
        "$<$<COMPILE_LANGUAGE:CXX>:${boost_Boost_random_COMPILE_OPTIONS_CXX_RELEASE}>")
endif ()
if (NOT "${boost_Boost_random_COMPILE_OPTIONS_C_RELEASE}" STREQUAL "")
    list(APPEND boost_Boost_random_COMPILE_OPTIONS_RELEASE
        "$<$<COMPILE_LANGUAGE:C>:${boost_Boost_random_COMPILE_OPTIONS_C_RELEASE}>")
endif ()
########### COMPONENT Boost::filesystem VARIABLES ############################################

set(boost_Boost_filesystem_INCLUDE_DIRS_RELEASE "${boost_PACKAGE_FOLDER_RELEASE}/include")
set(boost_Boost_filesystem_LIB_DIRS_RELEASE "${boost_PACKAGE_FOLDER_RELEASE}/lib")
set(boost_Boost_filesystem_BIN_DIRS_RELEASE "${boost_PACKAGE_FOLDER_RELEASE}/bin")
set(boost_Boost_filesystem_LIBRARY_TYPE_RELEASE SHARED)
set(boost_Boost_filesystem_IS_HOST_WINDOWS_RELEASE 1)
set(boost_Boost_filesystem_RES_DIRS_RELEASE )
set(boost_Boost_filesystem_DEFINITIONS_RELEASE )
set(boost_Boost_filesystem_OBJECTS_RELEASE )
set(boost_Boost_filesystem_COMPILE_DEFINITIONS_RELEASE )
set(boost_Boost_filesystem_COMPILE_OPTIONS_C_RELEASE "")
set(boost_Boost_filesystem_COMPILE_OPTIONS_CXX_RELEASE "")
set(boost_Boost_filesystem_LIBS_RELEASE boost_filesystem)
set(boost_Boost_filesystem_SYSTEM_LIBS_RELEASE )
set(boost_Boost_filesystem_FRAMEWORK_DIRS_RELEASE )
set(boost_Boost_filesystem_FRAMEWORKS_RELEASE )
set(boost_Boost_filesystem_DEPENDENCIES_RELEASE Boost::atomic Boost::system boost::_libboost)
set(boost_Boost_filesystem_SHARED_LINK_FLAGS_RELEASE )
set(boost_Boost_filesystem_EXE_LINK_FLAGS_RELEASE )
set(boost_Boost_filesystem_NO_SONAME_MODE_RELEASE FALSE)

# COMPOUND VARIABLES
set(boost_Boost_filesystem_LINKER_FLAGS_RELEASE)
if (NOT "${boost_Boost_filesystem_SHARED_LINK_FLAGS_RELEASE}" STREQUAL "")
    list(APPEND boost_Boost_filesystem_LINKER_FLAGS_RELEASE
        $<$<OR:$<STREQUAL:$<TARGET_PROPERTY:TYPE>,SHARED_LIBRARY>,$<STREQUAL:$<TARGET_PROPERTY:TYPE>,MODULE_LIBRARY>>:${boost_Boost_filesystem_SHARED_LINK_FLAGS_RELEASE}>)
endif ()
if (NOT "${boost_Boost_filesystem_EXE_LINK_FLAGS_RELEASE}" STREQUAL "")
    list(APPEND boost_Boost_filesystem_LINKER_FLAGS_RELEASE
        $<$<STREQUAL:$<TARGET_PROPERTY:TYPE>,EXECUTABLE>:${boost_Boost_filesystem_EXE_LINK_FLAGS_RELEASE}>)
endif ()
set(boost_Boost_filesystem_COMPILE_OPTIONS_RELEASE)
if (NOT "${boost_Boost_filesystem_COMPILE_OPTIONS_CXX_RELEASE}" STREQUAL "")
    list(APPEND boost_Boost_filesystem_COMPILE_OPTIONS_RELEASE
        "$<$<COMPILE_LANGUAGE:CXX>:${boost_Boost_filesystem_COMPILE_OPTIONS_CXX_RELEASE}>")
endif ()
if (NOT "${boost_Boost_filesystem_COMPILE_OPTIONS_C_RELEASE}" STREQUAL "")
    list(APPEND boost_Boost_filesystem_COMPILE_OPTIONS_RELEASE
        "$<$<COMPILE_LANGUAGE:C>:${boost_Boost_filesystem_COMPILE_OPTIONS_C_RELEASE}>")
endif ()
########### COMPONENT Boost::system VARIABLES ############################################

set(boost_Boost_system_INCLUDE_DIRS_RELEASE "${boost_PACKAGE_FOLDER_RELEASE}/include")
set(boost_Boost_system_LIB_DIRS_RELEASE "${boost_PACKAGE_FOLDER_RELEASE}/lib")
set(boost_Boost_system_BIN_DIRS_RELEASE "${boost_PACKAGE_FOLDER_RELEASE}/bin")
set(boost_Boost_system_LIBRARY_TYPE_RELEASE SHARED)
set(boost_Boost_system_IS_HOST_WINDOWS_RELEASE 1)
set(boost_Boost_system_RES_DIRS_RELEASE )
set(boost_Boost_system_DEFINITIONS_RELEASE )
set(boost_Boost_system_OBJECTS_RELEASE )
set(boost_Boost_system_COMPILE_DEFINITIONS_RELEASE )
set(boost_Boost_system_COMPILE_OPTIONS_C_RELEASE "")
set(boost_Boost_system_COMPILE_OPTIONS_CXX_RELEASE "")
set(boost_Boost_system_LIBS_RELEASE )
set(boost_Boost_system_SYSTEM_LIBS_RELEASE )
set(boost_Boost_system_FRAMEWORK_DIRS_RELEASE )
set(boost_Boost_system_FRAMEWORKS_RELEASE )
set(boost_Boost_system_DEPENDENCIES_RELEASE boost::_libboost)
set(boost_Boost_system_SHARED_LINK_FLAGS_RELEASE )
set(boost_Boost_system_EXE_LINK_FLAGS_RELEASE )
set(boost_Boost_system_NO_SONAME_MODE_RELEASE FALSE)

# COMPOUND VARIABLES
set(boost_Boost_system_LINKER_FLAGS_RELEASE)
if (NOT "${boost_Boost_system_SHARED_LINK_FLAGS_RELEASE}" STREQUAL "")
    list(APPEND boost_Boost_system_LINKER_FLAGS_RELEASE
        $<$<OR:$<STREQUAL:$<TARGET_PROPERTY:TYPE>,SHARED_LIBRARY>,$<STREQUAL:$<TARGET_PROPERTY:TYPE>,MODULE_LIBRARY>>:${boost_Boost_system_SHARED_LINK_FLAGS_RELEASE}>)
endif ()
if (NOT "${boost_Boost_system_EXE_LINK_FLAGS_RELEASE}" STREQUAL "")
    list(APPEND boost_Boost_system_LINKER_FLAGS_RELEASE
        $<$<STREQUAL:$<TARGET_PROPERTY:TYPE>,EXECUTABLE>:${boost_Boost_system_EXE_LINK_FLAGS_RELEASE}>)
endif ()
set(boost_Boost_system_COMPILE_OPTIONS_RELEASE)
if (NOT "${boost_Boost_system_COMPILE_OPTIONS_CXX_RELEASE}" STREQUAL "")
    list(APPEND boost_Boost_system_COMPILE_OPTIONS_RELEASE
        "$<$<COMPILE_LANGUAGE:CXX>:${boost_Boost_system_COMPILE_OPTIONS_CXX_RELEASE}>")
endif ()
if (NOT "${boost_Boost_system_COMPILE_OPTIONS_C_RELEASE}" STREQUAL "")
    list(APPEND boost_Boost_system_COMPILE_OPTIONS_RELEASE
        "$<$<COMPILE_LANGUAGE:C>:${boost_Boost_system_COMPILE_OPTIONS_C_RELEASE}>")
endif ()
########### COMPONENT Boost::regex VARIABLES ############################################

set(boost_Boost_regex_INCLUDE_DIRS_RELEASE "${boost_PACKAGE_FOLDER_RELEASE}/include")
set(boost_Boost_regex_LIB_DIRS_RELEASE "${boost_PACKAGE_FOLDER_RELEASE}/lib")
set(boost_Boost_regex_BIN_DIRS_RELEASE "${boost_PACKAGE_FOLDER_RELEASE}/bin")
set(boost_Boost_regex_LIBRARY_TYPE_RELEASE SHARED)
set(boost_Boost_regex_IS_HOST_WINDOWS_RELEASE 1)
set(boost_Boost_regex_RES_DIRS_RELEASE )
set(boost_Boost_regex_DEFINITIONS_RELEASE )
set(boost_Boost_regex_OBJECTS_RELEASE )
set(boost_Boost_regex_COMPILE_DEFINITIONS_RELEASE )
set(boost_Boost_regex_COMPILE_OPTIONS_C_RELEASE "")
set(boost_Boost_regex_COMPILE_OPTIONS_CXX_RELEASE "")
set(boost_Boost_regex_LIBS_RELEASE boost_regex)
set(boost_Boost_regex_SYSTEM_LIBS_RELEASE )
set(boost_Boost_regex_FRAMEWORK_DIRS_RELEASE )
set(boost_Boost_regex_FRAMEWORKS_RELEASE )
set(boost_Boost_regex_DEPENDENCIES_RELEASE boost::_libboost)
set(boost_Boost_regex_SHARED_LINK_FLAGS_RELEASE )
set(boost_Boost_regex_EXE_LINK_FLAGS_RELEASE )
set(boost_Boost_regex_NO_SONAME_MODE_RELEASE FALSE)

# COMPOUND VARIABLES
set(boost_Boost_regex_LINKER_FLAGS_RELEASE)
if (NOT "${boost_Boost_regex_SHARED_LINK_FLAGS_RELEASE}" STREQUAL "")
    list(APPEND boost_Boost_regex_LINKER_FLAGS_RELEASE
        $<$<OR:$<STREQUAL:$<TARGET_PROPERTY:TYPE>,SHARED_LIBRARY>,$<STREQUAL:$<TARGET_PROPERTY:TYPE>,MODULE_LIBRARY>>:${boost_Boost_regex_SHARED_LINK_FLAGS_RELEASE}>)
endif ()
if (NOT "${boost_Boost_regex_EXE_LINK_FLAGS_RELEASE}" STREQUAL "")
    list(APPEND boost_Boost_regex_LINKER_FLAGS_RELEASE
        $<$<STREQUAL:$<TARGET_PROPERTY:TYPE>,EXECUTABLE>:${boost_Boost_regex_EXE_LINK_FLAGS_RELEASE}>)
endif ()
set(boost_Boost_regex_COMPILE_OPTIONS_RELEASE)
if (NOT "${boost_Boost_regex_COMPILE_OPTIONS_CXX_RELEASE}" STREQUAL "")
    list(APPEND boost_Boost_regex_COMPILE_OPTIONS_RELEASE
        "$<$<COMPILE_LANGUAGE:CXX>:${boost_Boost_regex_COMPILE_OPTIONS_CXX_RELEASE}>")
endif ()
if (NOT "${boost_Boost_regex_COMPILE_OPTIONS_C_RELEASE}" STREQUAL "")
    list(APPEND boost_Boost_regex_COMPILE_OPTIONS_RELEASE
        "$<$<COMPILE_LANGUAGE:C>:${boost_Boost_regex_COMPILE_OPTIONS_C_RELEASE}>")
endif ()
########### COMPONENT Boost::program_options VARIABLES ############################################

set(boost_Boost_program_options_INCLUDE_DIRS_RELEASE "${boost_PACKAGE_FOLDER_RELEASE}/include")
set(boost_Boost_program_options_LIB_DIRS_RELEASE "${boost_PACKAGE_FOLDER_RELEASE}/lib")
set(boost_Boost_program_options_BIN_DIRS_RELEASE "${boost_PACKAGE_FOLDER_RELEASE}/bin")
set(boost_Boost_program_options_LIBRARY_TYPE_RELEASE SHARED)
set(boost_Boost_program_options_IS_HOST_WINDOWS_RELEASE 1)
set(boost_Boost_program_options_RES_DIRS_RELEASE )
set(boost_Boost_program_options_DEFINITIONS_RELEASE )
set(boost_Boost_program_options_OBJECTS_RELEASE )
set(boost_Boost_program_options_COMPILE_DEFINITIONS_RELEASE )
set(boost_Boost_program_options_COMPILE_OPTIONS_C_RELEASE "")
set(boost_Boost_program_options_COMPILE_OPTIONS_CXX_RELEASE "")
set(boost_Boost_program_options_LIBS_RELEASE boost_program_options)
set(boost_Boost_program_options_SYSTEM_LIBS_RELEASE )
set(boost_Boost_program_options_FRAMEWORK_DIRS_RELEASE )
set(boost_Boost_program_options_FRAMEWORKS_RELEASE )
set(boost_Boost_program_options_DEPENDENCIES_RELEASE boost::_libboost)
set(boost_Boost_program_options_SHARED_LINK_FLAGS_RELEASE )
set(boost_Boost_program_options_EXE_LINK_FLAGS_RELEASE )
set(boost_Boost_program_options_NO_SONAME_MODE_RELEASE FALSE)

# COMPOUND VARIABLES
set(boost_Boost_program_options_LINKER_FLAGS_RELEASE)
if (NOT "${boost_Boost_program_options_SHARED_LINK_FLAGS_RELEASE}" STREQUAL "")
    list(APPEND boost_Boost_program_options_LINKER_FLAGS_RELEASE
        $<$<OR:$<STREQUAL:$<TARGET_PROPERTY:TYPE>,SHARED_LIBRARY>,$<STREQUAL:$<TARGET_PROPERTY:TYPE>,MODULE_LIBRARY>>:${boost_Boost_program_options_SHARED_LINK_FLAGS_RELEASE}>)
endif ()
if (NOT "${boost_Boost_program_options_EXE_LINK_FLAGS_RELEASE}" STREQUAL "")
    list(APPEND boost_Boost_program_options_LINKER_FLAGS_RELEASE
        $<$<STREQUAL:$<TARGET_PROPERTY:TYPE>,EXECUTABLE>:${boost_Boost_program_options_EXE_LINK_FLAGS_RELEASE}>)
endif ()
set(boost_Boost_program_options_COMPILE_OPTIONS_RELEASE)
if (NOT "${boost_Boost_program_options_COMPILE_OPTIONS_CXX_RELEASE}" STREQUAL "")
    list(APPEND boost_Boost_program_options_COMPILE_OPTIONS_RELEASE
        "$<$<COMPILE_LANGUAGE:CXX>:${boost_Boost_program_options_COMPILE_OPTIONS_CXX_RELEASE}>")
endif ()
if (NOT "${boost_Boost_program_options_COMPILE_OPTIONS_C_RELEASE}" STREQUAL "")
    list(APPEND boost_Boost_program_options_COMPILE_OPTIONS_RELEASE
        "$<$<COMPILE_LANGUAGE:C>:${boost_Boost_program_options_COMPILE_OPTIONS_C_RELEASE}>")
endif ()
########### COMPONENT Boost::date_time VARIABLES ############################################

set(boost_Boost_date_time_INCLUDE_DIRS_RELEASE "${boost_PACKAGE_FOLDER_RELEASE}/include")
set(boost_Boost_date_time_LIB_DIRS_RELEASE "${boost_PACKAGE_FOLDER_RELEASE}/lib")
set(boost_Boost_date_time_BIN_DIRS_RELEASE "${boost_PACKAGE_FOLDER_RELEASE}/bin")
set(boost_Boost_date_time_LIBRARY_TYPE_RELEASE SHARED)
set(boost_Boost_date_time_IS_HOST_WINDOWS_RELEASE 1)
set(boost_Boost_date_time_RES_DIRS_RELEASE )
set(boost_Boost_date_time_DEFINITIONS_RELEASE )
set(boost_Boost_date_time_OBJECTS_RELEASE )
set(boost_Boost_date_time_COMPILE_DEFINITIONS_RELEASE )
set(boost_Boost_date_time_COMPILE_OPTIONS_C_RELEASE "")
set(boost_Boost_date_time_COMPILE_OPTIONS_CXX_RELEASE "")
set(boost_Boost_date_time_LIBS_RELEASE boost_date_time)
set(boost_Boost_date_time_SYSTEM_LIBS_RELEASE )
set(boost_Boost_date_time_FRAMEWORK_DIRS_RELEASE )
set(boost_Boost_date_time_FRAMEWORKS_RELEASE )
set(boost_Boost_date_time_DEPENDENCIES_RELEASE boost::_libboost)
set(boost_Boost_date_time_SHARED_LINK_FLAGS_RELEASE )
set(boost_Boost_date_time_EXE_LINK_FLAGS_RELEASE )
set(boost_Boost_date_time_NO_SONAME_MODE_RELEASE FALSE)

# COMPOUND VARIABLES
set(boost_Boost_date_time_LINKER_FLAGS_RELEASE)
if (NOT "${boost_Boost_date_time_SHARED_LINK_FLAGS_RELEASE}" STREQUAL "")
    list(APPEND boost_Boost_date_time_LINKER_FLAGS_RELEASE
        $<$<OR:$<STREQUAL:$<TARGET_PROPERTY:TYPE>,SHARED_LIBRARY>,$<STREQUAL:$<TARGET_PROPERTY:TYPE>,MODULE_LIBRARY>>:${boost_Boost_date_time_SHARED_LINK_FLAGS_RELEASE}>)
endif ()
if (NOT "${boost_Boost_date_time_EXE_LINK_FLAGS_RELEASE}" STREQUAL "")
    list(APPEND boost_Boost_date_time_LINKER_FLAGS_RELEASE
        $<$<STREQUAL:$<TARGET_PROPERTY:TYPE>,EXECUTABLE>:${boost_Boost_date_time_EXE_LINK_FLAGS_RELEASE}>)
endif ()
set(boost_Boost_date_time_COMPILE_OPTIONS_RELEASE)
if (NOT "${boost_Boost_date_time_COMPILE_OPTIONS_CXX_RELEASE}" STREQUAL "")
    list(APPEND boost_Boost_date_time_COMPILE_OPTIONS_RELEASE
        "$<$<COMPILE_LANGUAGE:CXX>:${boost_Boost_date_time_COMPILE_OPTIONS_CXX_RELEASE}>")
endif ()
if (NOT "${boost_Boost_date_time_COMPILE_OPTIONS_C_RELEASE}" STREQUAL "")
    list(APPEND boost_Boost_date_time_COMPILE_OPTIONS_RELEASE
        "$<$<COMPILE_LANGUAGE:C>:${boost_Boost_date_time_COMPILE_OPTIONS_C_RELEASE}>")
endif ()
########### COMPONENT Boost::atomic VARIABLES ############################################

set(boost_Boost_atomic_INCLUDE_DIRS_RELEASE "${boost_PACKAGE_FOLDER_RELEASE}/include")
set(boost_Boost_atomic_LIB_DIRS_RELEASE "${boost_PACKAGE_FOLDER_RELEASE}/lib")
set(boost_Boost_atomic_BIN_DIRS_RELEASE "${boost_PACKAGE_FOLDER_RELEASE}/bin")
set(boost_Boost_atomic_LIBRARY_TYPE_RELEASE SHARED)
set(boost_Boost_atomic_IS_HOST_WINDOWS_RELEASE 1)
set(boost_Boost_atomic_RES_DIRS_RELEASE )
set(boost_Boost_atomic_DEFINITIONS_RELEASE )
set(boost_Boost_atomic_OBJECTS_RELEASE )
set(boost_Boost_atomic_COMPILE_DEFINITIONS_RELEASE )
set(boost_Boost_atomic_COMPILE_OPTIONS_C_RELEASE "")
set(boost_Boost_atomic_COMPILE_OPTIONS_CXX_RELEASE "")
set(boost_Boost_atomic_LIBS_RELEASE boost_atomic)
set(boost_Boost_atomic_SYSTEM_LIBS_RELEASE )
set(boost_Boost_atomic_FRAMEWORK_DIRS_RELEASE )
set(boost_Boost_atomic_FRAMEWORKS_RELEASE )
set(boost_Boost_atomic_DEPENDENCIES_RELEASE boost::_libboost)
set(boost_Boost_atomic_SHARED_LINK_FLAGS_RELEASE )
set(boost_Boost_atomic_EXE_LINK_FLAGS_RELEASE )
set(boost_Boost_atomic_NO_SONAME_MODE_RELEASE FALSE)

# COMPOUND VARIABLES
set(boost_Boost_atomic_LINKER_FLAGS_RELEASE)
if (NOT "${boost_Boost_atomic_SHARED_LINK_FLAGS_RELEASE}" STREQUAL "")
    list(APPEND boost_Boost_atomic_LINKER_FLAGS_RELEASE
        $<$<OR:$<STREQUAL:$<TARGET_PROPERTY:TYPE>,SHARED_LIBRARY>,$<STREQUAL:$<TARGET_PROPERTY:TYPE>,MODULE_LIBRARY>>:${boost_Boost_atomic_SHARED_LINK_FLAGS_RELEASE}>)
endif ()
if (NOT "${boost_Boost_atomic_EXE_LINK_FLAGS_RELEASE}" STREQUAL "")
    list(APPEND boost_Boost_atomic_LINKER_FLAGS_RELEASE
        $<$<STREQUAL:$<TARGET_PROPERTY:TYPE>,EXECUTABLE>:${boost_Boost_atomic_EXE_LINK_FLAGS_RELEASE}>)
endif ()
set(boost_Boost_atomic_COMPILE_OPTIONS_RELEASE)
if (NOT "${boost_Boost_atomic_COMPILE_OPTIONS_CXX_RELEASE}" STREQUAL "")
    list(APPEND boost_Boost_atomic_COMPILE_OPTIONS_RELEASE
        "$<$<COMPILE_LANGUAGE:CXX>:${boost_Boost_atomic_COMPILE_OPTIONS_CXX_RELEASE}>")
endif ()
if (NOT "${boost_Boost_atomic_COMPILE_OPTIONS_C_RELEASE}" STREQUAL "")
    list(APPEND boost_Boost_atomic_COMPILE_OPTIONS_RELEASE
        "$<$<COMPILE_LANGUAGE:C>:${boost_Boost_atomic_COMPILE_OPTIONS_C_RELEASE}>")
endif ()
########### COMPONENT boost::_libboost VARIABLES ############################################

set(boost_boost__libboost_INCLUDE_DIRS_RELEASE "${boost_PACKAGE_FOLDER_RELEASE}/include")
set(boost_boost__libboost_LIB_DIRS_RELEASE "${boost_PACKAGE_FOLDER_RELEASE}/lib")
set(boost_boost__libboost_BIN_DIRS_RELEASE "${boost_PACKAGE_FOLDER_RELEASE}/bin")
set(boost_boost__libboost_LIBRARY_TYPE_RELEASE SHARED)
set(boost_boost__libboost_IS_HOST_WINDOWS_RELEASE 1)
set(boost_boost__libboost_RES_DIRS_RELEASE )
set(boost_boost__libboost_DEFINITIONS_RELEASE )
set(boost_boost__libboost_OBJECTS_RELEASE )
set(boost_boost__libboost_COMPILE_DEFINITIONS_RELEASE )
set(boost_boost__libboost_COMPILE_OPTIONS_C_RELEASE "")
set(boost_boost__libboost_COMPILE_OPTIONS_CXX_RELEASE "")
set(boost_boost__libboost_LIBS_RELEASE )
set(boost_boost__libboost_SYSTEM_LIBS_RELEASE bcrypt)
set(boost_boost__libboost_FRAMEWORK_DIRS_RELEASE )
set(boost_boost__libboost_FRAMEWORKS_RELEASE )
set(boost_boost__libboost_DEPENDENCIES_RELEASE Boost::headers)
set(boost_boost__libboost_SHARED_LINK_FLAGS_RELEASE )
set(boost_boost__libboost_EXE_LINK_FLAGS_RELEASE )
set(boost_boost__libboost_NO_SONAME_MODE_RELEASE FALSE)

# COMPOUND VARIABLES
set(boost_boost__libboost_LINKER_FLAGS_RELEASE)
if (NOT "${boost_boost__libboost_SHARED_LINK_FLAGS_RELEASE}" STREQUAL "")
    list(APPEND boost_boost__libboost_LINKER_FLAGS_RELEASE
        $<$<OR:$<STREQUAL:$<TARGET_PROPERTY:TYPE>,SHARED_LIBRARY>,$<STREQUAL:$<TARGET_PROPERTY:TYPE>,MODULE_LIBRARY>>:${boost_boost__libboost_SHARED_LINK_FLAGS_RELEASE}>)
endif ()
if (NOT "${boost_boost__libboost_EXE_LINK_FLAGS_RELEASE}" STREQUAL "")
    list(APPEND boost_boost__libboost_LINKER_FLAGS_RELEASE
        $<$<STREQUAL:$<TARGET_PROPERTY:TYPE>,EXECUTABLE>:${boost_boost__libboost_EXE_LINK_FLAGS_RELEASE}>)
endif ()
set(boost_boost__libboost_COMPILE_OPTIONS_RELEASE)
if (NOT "${boost_boost__libboost_COMPILE_OPTIONS_CXX_RELEASE}" STREQUAL "")
    list(APPEND boost_boost__libboost_COMPILE_OPTIONS_RELEASE
        "$<$<COMPILE_LANGUAGE:CXX>:${boost_boost__libboost_COMPILE_OPTIONS_CXX_RELEASE}>")
endif ()
if (NOT "${boost_boost__libboost_COMPILE_OPTIONS_C_RELEASE}" STREQUAL "")
    list(APPEND boost_boost__libboost_COMPILE_OPTIONS_RELEASE
        "$<$<COMPILE_LANGUAGE:C>:${boost_boost__libboost_COMPILE_OPTIONS_C_RELEASE}>")
endif ()
########### COMPONENT Boost::boost VARIABLES ############################################

set(boost_Boost_boost_INCLUDE_DIRS_RELEASE "${boost_PACKAGE_FOLDER_RELEASE}/include")
set(boost_Boost_boost_LIB_DIRS_RELEASE "${boost_PACKAGE_FOLDER_RELEASE}/lib")
set(boost_Boost_boost_BIN_DIRS_RELEASE "${boost_PACKAGE_FOLDER_RELEASE}/bin")
set(boost_Boost_boost_LIBRARY_TYPE_RELEASE SHARED)
set(boost_Boost_boost_IS_HOST_WINDOWS_RELEASE 1)
set(boost_Boost_boost_RES_DIRS_RELEASE )
set(boost_Boost_boost_DEFINITIONS_RELEASE )
set(boost_Boost_boost_OBJECTS_RELEASE )
set(boost_Boost_boost_COMPILE_DEFINITIONS_RELEASE )
set(boost_Boost_boost_COMPILE_OPTIONS_C_RELEASE "")
set(boost_Boost_boost_COMPILE_OPTIONS_CXX_RELEASE "")
set(boost_Boost_boost_LIBS_RELEASE )
set(boost_Boost_boost_SYSTEM_LIBS_RELEASE )
set(boost_Boost_boost_FRAMEWORK_DIRS_RELEASE )
set(boost_Boost_boost_FRAMEWORKS_RELEASE )
set(boost_Boost_boost_DEPENDENCIES_RELEASE Boost::headers)
set(boost_Boost_boost_SHARED_LINK_FLAGS_RELEASE )
set(boost_Boost_boost_EXE_LINK_FLAGS_RELEASE )
set(boost_Boost_boost_NO_SONAME_MODE_RELEASE FALSE)

# COMPOUND VARIABLES
set(boost_Boost_boost_LINKER_FLAGS_RELEASE)
if (NOT "${boost_Boost_boost_SHARED_LINK_FLAGS_RELEASE}" STREQUAL "")
    list(APPEND boost_Boost_boost_LINKER_FLAGS_RELEASE
        $<$<OR:$<STREQUAL:$<TARGET_PROPERTY:TYPE>,SHARED_LIBRARY>,$<STREQUAL:$<TARGET_PROPERTY:TYPE>,MODULE_LIBRARY>>:${boost_Boost_boost_SHARED_LINK_FLAGS_RELEASE}>)
endif ()
if (NOT "${boost_Boost_boost_EXE_LINK_FLAGS_RELEASE}" STREQUAL "")
    list(APPEND boost_Boost_boost_LINKER_FLAGS_RELEASE
        $<$<STREQUAL:$<TARGET_PROPERTY:TYPE>,EXECUTABLE>:${boost_Boost_boost_EXE_LINK_FLAGS_RELEASE}>)
endif ()
set(boost_Boost_boost_COMPILE_OPTIONS_RELEASE)
if (NOT "${boost_Boost_boost_COMPILE_OPTIONS_CXX_RELEASE}" STREQUAL "")
    list(APPEND boost_Boost_boost_COMPILE_OPTIONS_RELEASE
        "$<$<COMPILE_LANGUAGE:CXX>:${boost_Boost_boost_COMPILE_OPTIONS_CXX_RELEASE}>")
endif ()
if (NOT "${boost_Boost_boost_COMPILE_OPTIONS_C_RELEASE}" STREQUAL "")
    list(APPEND boost_Boost_boost_COMPILE_OPTIONS_RELEASE
        "$<$<COMPILE_LANGUAGE:C>:${boost_Boost_boost_COMPILE_OPTIONS_C_RELEASE}>")
endif ()
########### COMPONENT Boost::headers VARIABLES ############################################

set(boost_Boost_headers_INCLUDE_DIRS_RELEASE "${boost_PACKAGE_FOLDER_RELEASE}/include")
set(boost_Boost_headers_LIB_DIRS_RELEASE )
set(boost_Boost_headers_BIN_DIRS_RELEASE "${boost_PACKAGE_FOLDER_RELEASE}/bin")
set(boost_Boost_headers_LIBRARY_TYPE_RELEASE SHARED)
set(boost_Boost_headers_IS_HOST_WINDOWS_RELEASE 1)
set(boost_Boost_headers_RES_DIRS_RELEASE )
set(boost_Boost_headers_DEFINITIONS_RELEASE )
set(boost_Boost_headers_OBJECTS_RELEASE )
set(boost_Boost_headers_COMPILE_DEFINITIONS_RELEASE )
set(boost_Boost_headers_COMPILE_OPTIONS_C_RELEASE "")
set(boost_Boost_headers_COMPILE_OPTIONS_CXX_RELEASE "")
set(boost_Boost_headers_LIBS_RELEASE )
set(boost_Boost_headers_SYSTEM_LIBS_RELEASE )
set(boost_Boost_headers_FRAMEWORK_DIRS_RELEASE )
set(boost_Boost_headers_FRAMEWORKS_RELEASE )
set(boost_Boost_headers_DEPENDENCIES_RELEASE Boost::diagnostic_definitions Boost::disable_autolinking Boost::dynamic_linking)
set(boost_Boost_headers_SHARED_LINK_FLAGS_RELEASE )
set(boost_Boost_headers_EXE_LINK_FLAGS_RELEASE )
set(boost_Boost_headers_NO_SONAME_MODE_RELEASE FALSE)

# COMPOUND VARIABLES
set(boost_Boost_headers_LINKER_FLAGS_RELEASE)
if (NOT "${boost_Boost_headers_SHARED_LINK_FLAGS_RELEASE}" STREQUAL "")
    list(APPEND boost_Boost_headers_LINKER_FLAGS_RELEASE
        $<$<OR:$<STREQUAL:$<TARGET_PROPERTY:TYPE>,SHARED_LIBRARY>,$<STREQUAL:$<TARGET_PROPERTY:TYPE>,MODULE_LIBRARY>>:${boost_Boost_headers_SHARED_LINK_FLAGS_RELEASE}>)
endif ()
if (NOT "${boost_Boost_headers_EXE_LINK_FLAGS_RELEASE}" STREQUAL "")
    list(APPEND boost_Boost_headers_LINKER_FLAGS_RELEASE
        $<$<STREQUAL:$<TARGET_PROPERTY:TYPE>,EXECUTABLE>:${boost_Boost_headers_EXE_LINK_FLAGS_RELEASE}>)
endif ()
set(boost_Boost_headers_COMPILE_OPTIONS_RELEASE)
if (NOT "${boost_Boost_headers_COMPILE_OPTIONS_CXX_RELEASE}" STREQUAL "")
    list(APPEND boost_Boost_headers_COMPILE_OPTIONS_RELEASE
        "$<$<COMPILE_LANGUAGE:CXX>:${boost_Boost_headers_COMPILE_OPTIONS_CXX_RELEASE}>")
endif ()
if (NOT "${boost_Boost_headers_COMPILE_OPTIONS_C_RELEASE}" STREQUAL "")
    list(APPEND boost_Boost_headers_COMPILE_OPTIONS_RELEASE
        "$<$<COMPILE_LANGUAGE:C>:${boost_Boost_headers_COMPILE_OPTIONS_C_RELEASE}>")
endif ()
########### COMPONENT boost::process VARIABLES ############################################

set(boost_boost_process_INCLUDE_DIRS_RELEASE "${boost_PACKAGE_FOLDER_RELEASE}/include")
set(boost_boost_process_LIB_DIRS_RELEASE "${boost_PACKAGE_FOLDER_RELEASE}/lib")
set(boost_boost_process_BIN_DIRS_RELEASE "${boost_PACKAGE_FOLDER_RELEASE}/bin")
set(boost_boost_process_LIBRARY_TYPE_RELEASE SHARED)
set(boost_boost_process_IS_HOST_WINDOWS_RELEASE 1)
set(boost_boost_process_RES_DIRS_RELEASE )
set(boost_boost_process_DEFINITIONS_RELEASE "-DBOOST_PROCESS_DYN_LINK")
set(boost_boost_process_OBJECTS_RELEASE )
set(boost_boost_process_COMPILE_DEFINITIONS_RELEASE "BOOST_PROCESS_DYN_LINK")
set(boost_boost_process_COMPILE_OPTIONS_C_RELEASE "")
set(boost_boost_process_COMPILE_OPTIONS_CXX_RELEASE "")
set(boost_boost_process_LIBS_RELEASE )
set(boost_boost_process_SYSTEM_LIBS_RELEASE ntdll shell32 advapi32 user32)
set(boost_boost_process_FRAMEWORK_DIRS_RELEASE )
set(boost_boost_process_FRAMEWORKS_RELEASE )
set(boost_boost_process_DEPENDENCIES_RELEASE )
set(boost_boost_process_SHARED_LINK_FLAGS_RELEASE )
set(boost_boost_process_EXE_LINK_FLAGS_RELEASE )
set(boost_boost_process_NO_SONAME_MODE_RELEASE FALSE)

# COMPOUND VARIABLES
set(boost_boost_process_LINKER_FLAGS_RELEASE)
if (NOT "${boost_boost_process_SHARED_LINK_FLAGS_RELEASE}" STREQUAL "")
    list(APPEND boost_boost_process_LINKER_FLAGS_RELEASE
        $<$<OR:$<STREQUAL:$<TARGET_PROPERTY:TYPE>,SHARED_LIBRARY>,$<STREQUAL:$<TARGET_PROPERTY:TYPE>,MODULE_LIBRARY>>:${boost_boost_process_SHARED_LINK_FLAGS_RELEASE}>)
endif ()
if (NOT "${boost_boost_process_EXE_LINK_FLAGS_RELEASE}" STREQUAL "")
    list(APPEND boost_boost_process_LINKER_FLAGS_RELEASE
        $<$<STREQUAL:$<TARGET_PROPERTY:TYPE>,EXECUTABLE>:${boost_boost_process_EXE_LINK_FLAGS_RELEASE}>)
endif ()
set(boost_boost_process_COMPILE_OPTIONS_RELEASE)
if (NOT "${boost_boost_process_COMPILE_OPTIONS_CXX_RELEASE}" STREQUAL "")
    list(APPEND boost_boost_process_COMPILE_OPTIONS_RELEASE
        "$<$<COMPILE_LANGUAGE:CXX>:${boost_boost_process_COMPILE_OPTIONS_CXX_RELEASE}>")
endif ()
if (NOT "${boost_boost_process_COMPILE_OPTIONS_C_RELEASE}" STREQUAL "")
    list(APPEND boost_boost_process_COMPILE_OPTIONS_RELEASE
        "$<$<COMPILE_LANGUAGE:C>:${boost_boost_process_COMPILE_OPTIONS_C_RELEASE}>")
endif ()
########### COMPONENT Boost::dynamic_linking VARIABLES ############################################

set(boost_Boost_dynamic_linking_INCLUDE_DIRS_RELEASE "${boost_PACKAGE_FOLDER_RELEASE}/include")
set(boost_Boost_dynamic_linking_LIB_DIRS_RELEASE "${boost_PACKAGE_FOLDER_RELEASE}/lib")
set(boost_Boost_dynamic_linking_BIN_DIRS_RELEASE "${boost_PACKAGE_FOLDER_RELEASE}/bin")
set(boost_Boost_dynamic_linking_LIBRARY_TYPE_RELEASE SHARED)
set(boost_Boost_dynamic_linking_IS_HOST_WINDOWS_RELEASE 1)
set(boost_Boost_dynamic_linking_RES_DIRS_RELEASE )
set(boost_Boost_dynamic_linking_DEFINITIONS_RELEASE "-DBOOST_ALL_DYN_LINK")
set(boost_Boost_dynamic_linking_OBJECTS_RELEASE )
set(boost_Boost_dynamic_linking_COMPILE_DEFINITIONS_RELEASE "BOOST_ALL_DYN_LINK")
set(boost_Boost_dynamic_linking_COMPILE_OPTIONS_C_RELEASE "")
set(boost_Boost_dynamic_linking_COMPILE_OPTIONS_CXX_RELEASE "")
set(boost_Boost_dynamic_linking_LIBS_RELEASE )
set(boost_Boost_dynamic_linking_SYSTEM_LIBS_RELEASE )
set(boost_Boost_dynamic_linking_FRAMEWORK_DIRS_RELEASE )
set(boost_Boost_dynamic_linking_FRAMEWORKS_RELEASE )
set(boost_Boost_dynamic_linking_DEPENDENCIES_RELEASE )
set(boost_Boost_dynamic_linking_SHARED_LINK_FLAGS_RELEASE )
set(boost_Boost_dynamic_linking_EXE_LINK_FLAGS_RELEASE )
set(boost_Boost_dynamic_linking_NO_SONAME_MODE_RELEASE FALSE)

# COMPOUND VARIABLES
set(boost_Boost_dynamic_linking_LINKER_FLAGS_RELEASE)
if (NOT "${boost_Boost_dynamic_linking_SHARED_LINK_FLAGS_RELEASE}" STREQUAL "")
    list(APPEND boost_Boost_dynamic_linking_LINKER_FLAGS_RELEASE
        $<$<OR:$<STREQUAL:$<TARGET_PROPERTY:TYPE>,SHARED_LIBRARY>,$<STREQUAL:$<TARGET_PROPERTY:TYPE>,MODULE_LIBRARY>>:${boost_Boost_dynamic_linking_SHARED_LINK_FLAGS_RELEASE}>)
endif ()
if (NOT "${boost_Boost_dynamic_linking_EXE_LINK_FLAGS_RELEASE}" STREQUAL "")
    list(APPEND boost_Boost_dynamic_linking_LINKER_FLAGS_RELEASE
        $<$<STREQUAL:$<TARGET_PROPERTY:TYPE>,EXECUTABLE>:${boost_Boost_dynamic_linking_EXE_LINK_FLAGS_RELEASE}>)
endif ()
set(boost_Boost_dynamic_linking_COMPILE_OPTIONS_RELEASE)
if (NOT "${boost_Boost_dynamic_linking_COMPILE_OPTIONS_CXX_RELEASE}" STREQUAL "")
    list(APPEND boost_Boost_dynamic_linking_COMPILE_OPTIONS_RELEASE
        "$<$<COMPILE_LANGUAGE:CXX>:${boost_Boost_dynamic_linking_COMPILE_OPTIONS_CXX_RELEASE}>")
endif ()
if (NOT "${boost_Boost_dynamic_linking_COMPILE_OPTIONS_C_RELEASE}" STREQUAL "")
    list(APPEND boost_Boost_dynamic_linking_COMPILE_OPTIONS_RELEASE
        "$<$<COMPILE_LANGUAGE:C>:${boost_Boost_dynamic_linking_COMPILE_OPTIONS_C_RELEASE}>")
endif ()
########### COMPONENT Boost::disable_autolinking VARIABLES ############################################

set(boost_Boost_disable_autolinking_INCLUDE_DIRS_RELEASE "${boost_PACKAGE_FOLDER_RELEASE}/include")
set(boost_Boost_disable_autolinking_LIB_DIRS_RELEASE "${boost_PACKAGE_FOLDER_RELEASE}/lib")
set(boost_Boost_disable_autolinking_BIN_DIRS_RELEASE "${boost_PACKAGE_FOLDER_RELEASE}/bin")
set(boost_Boost_disable_autolinking_LIBRARY_TYPE_RELEASE SHARED)
set(boost_Boost_disable_autolinking_IS_HOST_WINDOWS_RELEASE 1)
set(boost_Boost_disable_autolinking_RES_DIRS_RELEASE )
set(boost_Boost_disable_autolinking_DEFINITIONS_RELEASE "-DBOOST_ALL_NO_LIB")
set(boost_Boost_disable_autolinking_OBJECTS_RELEASE )
set(boost_Boost_disable_autolinking_COMPILE_DEFINITIONS_RELEASE "BOOST_ALL_NO_LIB")
set(boost_Boost_disable_autolinking_COMPILE_OPTIONS_C_RELEASE "")
set(boost_Boost_disable_autolinking_COMPILE_OPTIONS_CXX_RELEASE "")
set(boost_Boost_disable_autolinking_LIBS_RELEASE )
set(boost_Boost_disable_autolinking_SYSTEM_LIBS_RELEASE )
set(boost_Boost_disable_autolinking_FRAMEWORK_DIRS_RELEASE )
set(boost_Boost_disable_autolinking_FRAMEWORKS_RELEASE )
set(boost_Boost_disable_autolinking_DEPENDENCIES_RELEASE )
set(boost_Boost_disable_autolinking_SHARED_LINK_FLAGS_RELEASE )
set(boost_Boost_disable_autolinking_EXE_LINK_FLAGS_RELEASE )
set(boost_Boost_disable_autolinking_NO_SONAME_MODE_RELEASE FALSE)

# COMPOUND VARIABLES
set(boost_Boost_disable_autolinking_LINKER_FLAGS_RELEASE)
if (NOT "${boost_Boost_disable_autolinking_SHARED_LINK_FLAGS_RELEASE}" STREQUAL "")
    list(APPEND boost_Boost_disable_autolinking_LINKER_FLAGS_RELEASE
        $<$<OR:$<STREQUAL:$<TARGET_PROPERTY:TYPE>,SHARED_LIBRARY>,$<STREQUAL:$<TARGET_PROPERTY:TYPE>,MODULE_LIBRARY>>:${boost_Boost_disable_autolinking_SHARED_LINK_FLAGS_RELEASE}>)
endif ()
if (NOT "${boost_Boost_disable_autolinking_EXE_LINK_FLAGS_RELEASE}" STREQUAL "")
    list(APPEND boost_Boost_disable_autolinking_LINKER_FLAGS_RELEASE
        $<$<STREQUAL:$<TARGET_PROPERTY:TYPE>,EXECUTABLE>:${boost_Boost_disable_autolinking_EXE_LINK_FLAGS_RELEASE}>)
endif ()
set(boost_Boost_disable_autolinking_COMPILE_OPTIONS_RELEASE)
if (NOT "${boost_Boost_disable_autolinking_COMPILE_OPTIONS_CXX_RELEASE}" STREQUAL "")
    list(APPEND boost_Boost_disable_autolinking_COMPILE_OPTIONS_RELEASE
        "$<$<COMPILE_LANGUAGE:CXX>:${boost_Boost_disable_autolinking_COMPILE_OPTIONS_CXX_RELEASE}>")
endif ()
if (NOT "${boost_Boost_disable_autolinking_COMPILE_OPTIONS_C_RELEASE}" STREQUAL "")
    list(APPEND boost_Boost_disable_autolinking_COMPILE_OPTIONS_RELEASE
        "$<$<COMPILE_LANGUAGE:C>:${boost_Boost_disable_autolinking_COMPILE_OPTIONS_C_RELEASE}>")
endif ()
########### COMPONENT Boost::diagnostic_definitions VARIABLES ############################################

set(boost_Boost_diagnostic_definitions_INCLUDE_DIRS_RELEASE "${boost_PACKAGE_FOLDER_RELEASE}/include")
set(boost_Boost_diagnostic_definitions_LIB_DIRS_RELEASE "${boost_PACKAGE_FOLDER_RELEASE}/lib")
set(boost_Boost_diagnostic_definitions_BIN_DIRS_RELEASE "${boost_PACKAGE_FOLDER_RELEASE}/bin")
set(boost_Boost_diagnostic_definitions_LIBRARY_TYPE_RELEASE SHARED)
set(boost_Boost_diagnostic_definitions_IS_HOST_WINDOWS_RELEASE 1)
set(boost_Boost_diagnostic_definitions_RES_DIRS_RELEASE )
set(boost_Boost_diagnostic_definitions_DEFINITIONS_RELEASE )
set(boost_Boost_diagnostic_definitions_OBJECTS_RELEASE )
set(boost_Boost_diagnostic_definitions_COMPILE_DEFINITIONS_RELEASE )
set(boost_Boost_diagnostic_definitions_COMPILE_OPTIONS_C_RELEASE "")
set(boost_Boost_diagnostic_definitions_COMPILE_OPTIONS_CXX_RELEASE "")
set(boost_Boost_diagnostic_definitions_LIBS_RELEASE )
set(boost_Boost_diagnostic_definitions_SYSTEM_LIBS_RELEASE )
set(boost_Boost_diagnostic_definitions_FRAMEWORK_DIRS_RELEASE )
set(boost_Boost_diagnostic_definitions_FRAMEWORKS_RELEASE )
set(boost_Boost_diagnostic_definitions_DEPENDENCIES_RELEASE )
set(boost_Boost_diagnostic_definitions_SHARED_LINK_FLAGS_RELEASE )
set(boost_Boost_diagnostic_definitions_EXE_LINK_FLAGS_RELEASE )
set(boost_Boost_diagnostic_definitions_NO_SONAME_MODE_RELEASE FALSE)

# COMPOUND VARIABLES
set(boost_Boost_diagnostic_definitions_LINKER_FLAGS_RELEASE)
if (NOT "${boost_Boost_diagnostic_definitions_SHARED_LINK_FLAGS_RELEASE}" STREQUAL "")
    list(APPEND boost_Boost_diagnostic_definitions_LINKER_FLAGS_RELEASE
        $<$<OR:$<STREQUAL:$<TARGET_PROPERTY:TYPE>,SHARED_LIBRARY>,$<STREQUAL:$<TARGET_PROPERTY:TYPE>,MODULE_LIBRARY>>:${boost_Boost_diagnostic_definitions_SHARED_LINK_FLAGS_RELEASE}>)
endif ()
if (NOT "${boost_Boost_diagnostic_definitions_EXE_LINK_FLAGS_RELEASE}" STREQUAL "")
    list(APPEND boost_Boost_diagnostic_definitions_LINKER_FLAGS_RELEASE
        $<$<STREQUAL:$<TARGET_PROPERTY:TYPE>,EXECUTABLE>:${boost_Boost_diagnostic_definitions_EXE_LINK_FLAGS_RELEASE}>)
endif ()
set(boost_Boost_diagnostic_definitions_COMPILE_OPTIONS_RELEASE)
if (NOT "${boost_Boost_diagnostic_definitions_COMPILE_OPTIONS_CXX_RELEASE}" STREQUAL "")
    list(APPEND boost_Boost_diagnostic_definitions_COMPILE_OPTIONS_RELEASE
        "$<$<COMPILE_LANGUAGE:CXX>:${boost_Boost_diagnostic_definitions_COMPILE_OPTIONS_CXX_RELEASE}>")
endif ()
if (NOT "${boost_Boost_diagnostic_definitions_COMPILE_OPTIONS_C_RELEASE}" STREQUAL "")
    list(APPEND boost_Boost_diagnostic_definitions_COMPILE_OPTIONS_RELEASE
        "$<$<COMPILE_LANGUAGE:C>:${boost_Boost_diagnostic_definitions_COMPILE_OPTIONS_C_RELEASE}>")
endif ()