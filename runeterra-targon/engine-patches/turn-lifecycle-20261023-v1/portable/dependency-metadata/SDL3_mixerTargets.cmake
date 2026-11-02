# Load the debug and release variables
file(GLOB DATA_FILES "${CMAKE_CURRENT_LIST_DIR}/SDL3_mixer-*-data.cmake")

foreach(f ${DATA_FILES})
    include(${f})
endforeach()

# Create the targets for all the components
foreach(_COMPONENT ${sdl_mixer_COMPONENT_NAMES} )
    if(NOT TARGET ${_COMPONENT})
        add_library(${_COMPONENT} INTERFACE IMPORTED)
        message(${SDL3_mixer_MESSAGE_MODE} "Conan: Component target declared '${_COMPONENT}'")
    endif()
endforeach()

if(NOT TARGET SDL3_mixer::SDL3_mixer)
    add_library(SDL3_mixer::SDL3_mixer INTERFACE IMPORTED)
    message(${SDL3_mixer_MESSAGE_MODE} "Conan: Target declared 'SDL3_mixer::SDL3_mixer'")
endif()
# Load the debug and release library finders
file(GLOB CONFIG_FILES "${CMAKE_CURRENT_LIST_DIR}/SDL3_mixer-Target-*.cmake")

foreach(f ${CONFIG_FILES})
    include(${f})
endforeach()