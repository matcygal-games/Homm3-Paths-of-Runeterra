# Conan automatically generated toolchain file
# DO NOT EDIT MANUALLY, it will be overwritten

# Avoid including toolchain file several times (bad if appending to variables like
#   CMAKE_CXX_FLAGS. See https://github.com/android/ndk/issues/323
include_guard()
message(STATUS "Using Conan toolchain: ${CMAKE_CURRENT_LIST_FILE}")
if(${CMAKE_VERSION} VERSION_LESS "3.15")
    message(FATAL_ERROR "The 'CMakeToolchain' generator only works with CMake >= 3.15")
endif()

########## 'user_toolchain' block #############
# Include one or more CMake user toolchain from tools.cmake.cmaketoolchain:user_toolchain



########## 'generic_system' block #############
# Definition of system, platform and toolset





########## 'compilers' block #############

set(CMAKE_C_COMPILER "cl")
set(CMAKE_CXX_COMPILER "cl")


########## 'rpath_link_flags' block #############
# Pass -rpath-link pointing to all directories with runtime libraries


########## 'libcxx' block #############
# Definition of libcxx from 'compiler.libcxx' setting, defining the
# right CXX_FLAGS for that libcxx



########## 'vs_runtime' block #############
# Definition of VS runtime CMAKE_MSVC_RUNTIME_LIBRARY, from settings build_type,
# compiler.runtime, compiler.runtime_type

cmake_policy(GET CMP0091 POLICY_CMP0091)
if(NOT "${POLICY_CMP0091}" STREQUAL NEW)
    message(FATAL_ERROR "The CMake policy CMP0091 must be NEW, but is '${POLICY_CMP0091}'")
endif()
message(STATUS "Conan toolchain: Setting CMAKE_MSVC_RUNTIME_LIBRARY=$<$<CONFIG:Release>:MultiThreadedDLL>")
set(CMAKE_MSVC_RUNTIME_LIBRARY "$<$<CONFIG:Release>:MultiThreadedDLL>")


########## 'cppstd' block #############
# Define the C++ and C standards from 'compiler.cppstd' and 'compiler.cstd'

function(conan_modify_std_watch variable access value current_list_file stack)
    set(conan_watched_std_variable "20")
    if (${variable} STREQUAL "CMAKE_C_STANDARD")
        set(conan_watched_std_variable "")
    endif()
    if ("${access}" STREQUAL "MODIFIED_ACCESS" AND NOT "${value}" STREQUAL "${conan_watched_std_variable}")
        message(STATUS "Warning: Standard ${variable} value defined in conan_toolchain.cmake to ${conan_watched_std_variable} has been modified to ${value} by ${current_list_file}")
    endif()
    unset(conan_watched_std_variable)
endfunction()

message(STATUS "Conan toolchain: C++ Standard 20 with extensions OFF")
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
variable_watch(CMAKE_CXX_STANDARD conan_modify_std_watch)


########## 'extra_flags' block #############
# Include extra C++, C and linker flags from configuration tools.build:<type>flags
# and from CMakeToolchain.extra_<type>_flags

# Conan conf flags start: 
add_compile_definitions( "_WIN32_WINNT=0x0601" "WINVER=0x0601" "NTDDI_VERSION=0x06010000")
# Conan conf flags end


########## 'cmake_flags_init' block #############
# Define CMAKE_<XXX>_FLAGS from CONAN_<XXX>_FLAGS

foreach(config IN LISTS CMAKE_CONFIGURATION_TYPES)
    string(TOUPPER ${config} config)
    if(DEFINED CONAN_CXX_FLAGS_${config})
      string(APPEND CMAKE_CXX_FLAGS_${config}_INIT " ${CONAN_CXX_FLAGS_${config}}")
    endif()
    if(DEFINED CONAN_C_FLAGS_${config})
      string(APPEND CMAKE_C_FLAGS_${config}_INIT " ${CONAN_C_FLAGS_${config}}")
    endif()
    if(DEFINED CONAN_ASM_FLAGS_${config})
      string(APPEND CMAKE_ASM_FLAGS_${config}_INIT " ${CONAN_ASM_FLAGS_${config}}")
    endif()
    if(DEFINED CONAN_SHARED_LINKER_FLAGS_${config})
      string(APPEND CMAKE_SHARED_LINKER_FLAGS_${config}_INIT " ${CONAN_SHARED_LINKER_FLAGS_${config}}")
    endif()
    if(DEFINED CONAN_EXE_LINKER_FLAGS_${config})
      string(APPEND CMAKE_EXE_LINKER_FLAGS_${config}_INIT " ${CONAN_EXE_LINKER_FLAGS_${config}}")
    endif()
    if(DEFINED CONAN_RC_FLAGS_${config})
      string(APPEND CMAKE_RC_FLAGS_${config}_INIT " ${CONAN_RC_FLAGS_${config}}")
    endif()
endforeach()

if(DEFINED CONAN_CXX_FLAGS)
  string(APPEND CMAKE_CXX_FLAGS_INIT " ${CONAN_CXX_FLAGS}")
endif()
if(DEFINED CONAN_C_FLAGS)
  string(APPEND CMAKE_C_FLAGS_INIT " ${CONAN_C_FLAGS}")
endif()
if(DEFINED CONAN_ASM_FLAGS)
  string(APPEND CMAKE_ASM_FLAGS_INIT " ${CONAN_ASM_FLAGS}")
endif()
if(DEFINED CONAN_SHARED_LINKER_FLAGS)
  string(APPEND CMAKE_SHARED_LINKER_FLAGS_INIT " ${CONAN_SHARED_LINKER_FLAGS}")
endif()
if(DEFINED CONAN_EXE_LINKER_FLAGS)
  string(APPEND CMAKE_EXE_LINKER_FLAGS_INIT " ${CONAN_EXE_LINKER_FLAGS}")
endif()
if(DEFINED CONAN_RC_FLAGS)
  string(APPEND CMAKE_RC_FLAGS_INIT " ${CONAN_RC_FLAGS}")
endif()
if(DEFINED CONAN_OBJCXX_FLAGS)
  string(APPEND CMAKE_OBJCXX_FLAGS_INIT " ${CONAN_OBJCXX_FLAGS}")
endif()
if(DEFINED CONAN_OBJC_FLAGS)
  string(APPEND CMAKE_OBJC_FLAGS_INIT " ${CONAN_OBJC_FLAGS}")
endif()


########## 'extra_variables' block #############
# Definition of extra CMake variables from tools.cmake.cmaketoolchain:extra_variables



########## 'try_compile' block #############
# Blocks after this one will not be added when running CMake try/checks
get_property( _CMAKE_IN_TRY_COMPILE GLOBAL PROPERTY IN_TRY_COMPILE )
if(_CMAKE_IN_TRY_COMPILE)
    message(STATUS "Running toolchain IN_TRY_COMPILE")
    return()
endif()


########## 'find_paths' block #############
# Define paths to find packages, programs, libraries, etc.
if(EXISTS "${CMAKE_CURRENT_LIST_DIR}/conan_cmakedeps_paths.cmake")
  message(STATUS "Conan toolchain: Including CMakeConfigDeps generated conan_cmakedeps_paths.cmake")
  include("${CMAKE_CURRENT_LIST_DIR}/conan_cmakedeps_paths.cmake")
else()

set(CMAKE_FIND_PACKAGE_PREFER_CONFIG ON)

# Definition of CMAKE_MODULE_PATH
list(PREPEND CMAKE_MODULE_PATH "<SDK_ROOT>/conan-home/p/qtde84f76087842/p/lib/cmake/Qt5Widgets" "<SDK_ROOT>/conan-home/p/qtde84f76087842/p/lib/cmake/Qt5Gui" "<SDK_ROOT>/conan-home/p/qtde84f76087842/p/lib/cmake/Qt5LinguistTools" "<SDK_ROOT>/conan-home/p/qtde84f76087842/p/bin" "<SDK_ROOT>/conan-home/p/qtde84f76087842/p/lib/cmake/Qt5Core")
# the generators folder (where conan generates files, like this toolchain)
list(PREPEND CMAKE_MODULE_PATH ${CMAKE_CURRENT_LIST_DIR})

# Definition of CMAKE_PREFIX_PATH, CMAKE_XXXXX_PATH
# The explicitly defined "builddirs" of "host" context dependencies must be in PREFIX_PATH
list(PREPEND CMAKE_PREFIX_PATH "<SDK_ROOT>/conan-home/p/qtde84f76087842/p/lib/cmake/Qt5Widgets" "<SDK_ROOT>/conan-home/p/qtde84f76087842/p/lib/cmake/Qt5Gui" "<SDK_ROOT>/conan-home/p/qtde84f76087842/p/lib/cmake/Qt5LinguistTools" "<SDK_ROOT>/conan-home/p/qtde84f76087842/p/bin" "<SDK_ROOT>/conan-home/p/qtde84f76087842/p/lib/cmake/Qt5Core")
# The Conan local "generators" folder, where this toolchain is saved.
list(PREPEND CMAKE_PREFIX_PATH ${CMAKE_CURRENT_LIST_DIR} )
list(PREPEND CMAKE_LIBRARY_PATH "<SDK_ROOT>/conan-home/p/minizf455d3a92e5f9/p/lib" "<SDK_ROOT>/conan-home/p/libsqafe0e43ae7ecc/p/lib" "<SDK_ROOT>/conan-home/p/onetbeec24a0b9e43d/p/lib" "<SDK_ROOT>/conan-home/p/sdl_i44042adf09a1b/p/lib" "<SDK_ROOT>/conan-home/p/sdl_ma71c9f6f2fcfe/p/lib" "<SDK_ROOT>/conan-home/p/flac50f7f796e5196/p/lib" "<SDK_ROOT>/conan-home/p/opusf3ecbcabf2871d/p/lib" "<SDK_ROOT>/conan-home/p/mpg1217a881f030e0f/p/lib" "<SDK_ROOT>/conan-home/p/ogg5ed6d81817e4c/p/lib" "<SDK_ROOT>/conan-home/p/sdl_td9fee9bb38b98/p/lib" "<SDK_ROOT>/conan-home/p/plutoeb4cf45b4d267/p/lib" "lib" "<SDK_ROOT>/conan-home/p/freetf9f0ea006fb2c/p/lib" "lib" "<SDK_ROOT>/conan-home/p/boost2daea649742b4/p/lib" "<SDK_ROOT>/conan-home/p/luajicb3d27f823ff2/p/lib" "<SDK_ROOT>/conan-home/p/ffmpe58f6e49b85723/p/lib" "<SDK_ROOT>/conan-home/p/bzip229180355bba12/p/lib" "<SDK_ROOT>/conan-home/p/xz_ut74796b4afa323/p/lib" "<SDK_ROOT>/conan-home/p/opusa6deb694451ce/p/lib" "lib" "<SDK_ROOT>/conan-home/p/sdl0eecc6fcfc36a/p/lib" "<SDK_ROOT>/conan-home/p/libica3ca054de0149/p/lib" "<SDK_ROOT>/conan-home/p/qtde84f76087842/p/lib" "<SDK_ROOT>/conan-home/p/qtde84f76087842/p/plugins/styles" "<SDK_ROOT>/conan-home/p/qtde84f76087842/p/plugins/platforms" "<SDK_ROOT>/conan-home/p/qtde84f76087842/p/plugins/imageformats" "<SDK_ROOT>/conan-home/p/qtde84f76087842/p/plugins/iconengines" "<SDK_ROOT>/conan-home/p/qtde84f76087842/p/plugins/sqldrivers" "lib" "lib" "<SDK_ROOT>/conan-home/p/libpnea4a3e718b3d7/p/lib" "lib" "lib" "lib" "<SDK_ROOT>/conan-home/p/libcu421ab03bf8dff/p/lib" "<SDK_ROOT>/conan-home/p/zlib705a7ddfe2543/p/lib")
list(PREPEND CMAKE_INCLUDE_PATH "<SDK_ROOT>/conan-home/p/minizf455d3a92e5f9/p/include" "<SDK_ROOT>/conan-home/p/minizf455d3a92e5f9/p/include/minizip" "<SDK_ROOT>/conan-home/p/libsqafe0e43ae7ecc/p/include" "<SDK_ROOT>/conan-home/p/onetbeec24a0b9e43d/p/include" "<SDK_ROOT>/conan-home/p/sdl_i44042adf09a1b/p/include" "<SDK_ROOT>/conan-home/p/sdl_ma71c9f6f2fcfe/p/include" "<SDK_ROOT>/conan-home/p/flac50f7f796e5196/p/include" "<SDK_ROOT>/conan-home/p/opusf3ecbcabf2871d/p/include" "<SDK_ROOT>/conan-home/p/opusf3ecbcabf2871d/p/include/opus" "<SDK_ROOT>/conan-home/p/mpg1217a881f030e0f/p/include" "<SDK_ROOT>/conan-home/p/ogg5ed6d81817e4c/p/include" "<SDK_ROOT>/conan-home/p/sdl_td9fee9bb38b98/p/include" "<SDK_ROOT>/conan-home/p/plutoeb4cf45b4d267/p/include/plutosvg" "include" "<SDK_ROOT>/conan-home/p/freetf9f0ea006fb2c/p/include" "<SDK_ROOT>/conan-home/p/freetf9f0ea006fb2c/p/include/freetype2" "include" "<SDK_ROOT>/conan-home/p/boost2daea649742b4/p/include" "<SDK_ROOT>/conan-home/p/luajicb3d27f823ff2/p/include/luajit-2.1" "<SDK_ROOT>/conan-home/p/ffmpe58f6e49b85723/p/include" "<SDK_ROOT>/conan-home/p/bzip229180355bba12/p/include" "<SDK_ROOT>/conan-home/p/xz_ut74796b4afa323/p/include" "<SDK_ROOT>/conan-home/p/opusa6deb694451ce/p/include" "<SDK_ROOT>/conan-home/p/opusa6deb694451ce/p/include/opus" "include" "<SDK_ROOT>/conan-home/p/sdl0eecc6fcfc36a/p/include" "<SDK_ROOT>/conan-home/p/libica3ca054de0149/p/include" "<SDK_ROOT>/conan-home/p/qtde84f76087842/p/include" "<SDK_ROOT>/conan-home/p/qtde84f76087842/p/include/QtDesigner" "<SDK_ROOT>/conan-home/p/qtde84f76087842/p/include/QtUiTools" "<SDK_ROOT>/conan-home/p/qtde84f76087842/p/include/QtHelp" "<SDK_ROOT>/conan-home/p/qtde84f76087842/p/include/QtUiPlugin" "<SDK_ROOT>/conan-home/p/qtde84f76087842/p/include/QtPrintSupport" "<SDK_ROOT>/conan-home/p/qtde84f76087842/p/include/QtSvg" "<SDK_ROOT>/conan-home/p/qtde84f76087842/p/include/QtOpenGLExtensions" "<SDK_ROOT>/conan-home/p/qtde84f76087842/p/include/QtOpenGL" "<SDK_ROOT>/conan-home/p/qtde84f76087842/p/include/QtWindowsUIAutomationSupport" "<SDK_ROOT>/conan-home/p/qtde84f76087842/p/include/QtWidgets" "<SDK_ROOT>/conan-home/p/qtde84f76087842/p/include/QtAccessibilitySupport" "<SDK_ROOT>/conan-home/p/qtde84f76087842/p/include/QtThemeSupport" "<SDK_ROOT>/conan-home/p/qtde84f76087842/p/include/QtFontDatabaseSupport" "<SDK_ROOT>/conan-home/p/qtde84f76087842/p/include/QtEventDispatcherSupport" "<SDK_ROOT>/conan-home/p/qtde84f76087842/p/include/QtXml" "<SDK_ROOT>/conan-home/p/qtde84f76087842/p/include/QtConcurrent" "<SDK_ROOT>/conan-home/p/qtde84f76087842/p/include/QtTest" "<SDK_ROOT>/conan-home/p/qtde84f76087842/p/include/QtSql" "<SDK_ROOT>/conan-home/p/qtde84f76087842/p/include/QtNetwork" "<SDK_ROOT>/conan-home/p/qtde84f76087842/p/include/QtGui" "<SDK_ROOT>/conan-home/p/qtde84f76087842/p/include/QtCore" "<SDK_ROOT>/conan-home/p/qtde84f76087842/p/mkspecs/win32-msvc" "include" "include" "<SDK_ROOT>/conan-home/p/libpnea4a3e718b3d7/p/include" "include" "include" "include" "<SDK_ROOT>/conan-home/p/libcu421ab03bf8dff/p/include" "<SDK_ROOT>/conan-home/p/zlib705a7ddfe2543/p/include")
set(CONAN_RUNTIME_LIB_DIRS "<SDK_ROOT>/conan-home/p/minizf455d3a92e5f9/p/bin" "<SDK_ROOT>/conan-home/p/libsqafe0e43ae7ecc/p/bin" "<SDK_ROOT>/conan-home/p/onetbeec24a0b9e43d/p/bin" "<SDK_ROOT>/conan-home/p/sdl_i44042adf09a1b/p/bin" "<SDK_ROOT>/conan-home/p/sdl_ma71c9f6f2fcfe/p/bin" "<SDK_ROOT>/conan-home/p/flac50f7f796e5196/p/bin" "<SDK_ROOT>/conan-home/p/opusf3ecbcabf2871d/p/bin" "<SDK_ROOT>/conan-home/p/mpg1217a881f030e0f/p/bin" "<SDK_ROOT>/conan-home/p/ogg5ed6d81817e4c/p/bin" "<SDK_ROOT>/conan-home/p/sdl_td9fee9bb38b98/p/bin" "<SDK_ROOT>/conan-home/p/plutoeb4cf45b4d267/p/bin" "bin" "<SDK_ROOT>/conan-home/p/freetf9f0ea006fb2c/p/bin" "bin" "<SDK_ROOT>/conan-home/p/boost2daea649742b4/p/bin" "<SDK_ROOT>/conan-home/p/luajicb3d27f823ff2/p/bin" "<SDK_ROOT>/conan-home/p/ffmpe58f6e49b85723/p/bin" "<SDK_ROOT>/conan-home/p/bzip229180355bba12/p/bin" "<SDK_ROOT>/conan-home/p/xz_ut74796b4afa323/p/bin" "<SDK_ROOT>/conan-home/p/opusa6deb694451ce/p/bin" "bin" "<SDK_ROOT>/conan-home/p/sdl0eecc6fcfc36a/p/bin" "<SDK_ROOT>/conan-home/p/libica3ca054de0149/p/bin" "<SDK_ROOT>/conan-home/p/qtde84f76087842/p/bin" "bin" "bin" "<SDK_ROOT>/conan-home/p/libpnea4a3e718b3d7/p/bin" "bin" "bin" "bin" "<SDK_ROOT>/conan-home/p/libcu421ab03bf8dff/p/bin" "<SDK_ROOT>/conan-home/p/zlib705a7ddfe2543/p/bin" )

endif()


########## 'pkg_config' block #############
# Define pkg-config from 'tools.gnu:pkg_config' executable and paths

if (DEFINED ENV{PKG_CONFIG_PATH})
set(ENV{PKG_CONFIG_PATH} "${CMAKE_CURRENT_LIST_DIR};$ENV{PKG_CONFIG_PATH}")
else()
set(ENV{PKG_CONFIG_PATH} "${CMAKE_CURRENT_LIST_DIR};")
endif()


########## 'rpath' block #############
# Defining CMAKE_SKIP_RPATH



########## 'output_dirs' block #############
# Definition of CMAKE_INSTALL_XXX folders

# Ensure export(PACKAGE) honors CMAKE_EXPORT_PACKAGE_REGISTRY even if the
# project sets cmake_minimum_required() lower than 3.15.
cmake_policy(SET CMP0090 NEW)
if(NOT DEFINED CMAKE_EXPORT_PACKAGE_REGISTRY)
    set(CMAKE_EXPORT_PACKAGE_REGISTRY OFF)
endif()

set(CMAKE_INSTALL_BINDIR "bin")
set(CMAKE_INSTALL_SBINDIR "bin")
set(CMAKE_INSTALL_LIBEXECDIR "bin")
set(CMAKE_INSTALL_LIBDIR "lib")
set(CMAKE_INSTALL_INCLUDEDIR "include")
set(CMAKE_INSTALL_OLDINCLUDEDIR "include")


########## 'variables' block #############
# Definition of CMake variables from CMakeToolchain.variables values

# Variables
set(USING_CONAN ON CACHE BOOL "Variable USING_CONAN conan-toolchain defined")
set(CONAN_RUNTIME_LIBS_FILE "<SDK_ROOT>/conan-generated/_runtime_libs.txt" CACHE STRING "Variable CONAN_RUNTIME_LIBS_FILE conan-toolchain defined")
set(CONAN_ZLIB_DIR "<SDK_ROOT>/conan-home/p/zlib705a7ddfe2543/p/bin" CACHE STRING "Variable CONAN_ZLIB_DIR conan-toolchain defined")
# Variables  per configuration



########## 'preprocessor' block #############
# Preprocessor definitions from CMakeToolchain.preprocessor_definitions values

# Preprocessor definitions per configuration



if(CMAKE_POLICY_DEFAULT_CMP0091)  # Avoid unused and not-initialized warnings
endif()
