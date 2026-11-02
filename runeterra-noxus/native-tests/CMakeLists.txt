cmake_minimum_required(VERSION 3.25)
project(noxus_native_lab LANGUAGES CXX)
if(NOT DEFINED NATIVE_PLAN)
  message(FATAL_ERROR "Use scripts/native_lab.py build to bind sealed native inputs")
endif()
include("${NATIVE_PLAN}")
add_executable(noxus_native_lab
  NoxusControlledTest.cpp
  "${ENGINE_SOURCE}/test/main.cpp"
  "${ENGINE_SOURCE}/test/CVcmiTestConfig.cpp"
  "${ENGINE_SOURCE}/test/mock/TinyMapGameTest.cpp"
  "${ENGINE_SOURCE}/test/mock/TinyH3MBuilder.cpp"
  "${ENGINE_SOURCE}/test/mock/TinyH3MWriter.cpp"
  "${ENGINE_SOURCE}/test/mock/mock_MapServiceTinyH3M.cpp"
  "${ENGINE_SOURCE}/test/server/battles/BattleTestFixture.cpp"
  ${NATIVE_OBJECTS})
target_include_directories(noxus_native_lab PRIVATE ${NATIVE_INCLUDES} "${ENGINE_SOURCE}/test/mock")
target_compile_definitions(noxus_native_lab PRIVATE ${NATIVE_DEFINES} VCMI_DLL_STATIC)
target_compile_features(noxus_native_lab PRIVATE cxx_std_20)
target_compile_options(noxus_native_lab PRIVATE /bigobj /utf-8 /EHsc /GR /wd4250 /wd4251 /wd4244 /wd4267 /wd4275)
set_property(TARGET noxus_native_lab PROPERTY MSVC_RUNTIME_LIBRARY MultiThreadedDLL)
target_link_libraries(noxus_native_lab PRIVATE ${NATIVE_LIBRARIES})
target_link_options(noxus_native_lab PRIVATE /INCREMENTAL:NO /OPT:REF /OPT:ICF)
set_target_properties(noxus_native_lab PROPERTIES RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin")
