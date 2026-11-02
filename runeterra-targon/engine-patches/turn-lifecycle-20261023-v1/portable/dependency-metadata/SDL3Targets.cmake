# Load the debug and release variables
file(GLOB DATA_FILES "${CMAKE_CURRENT_LIST_DIR}/SDL3-*-data.cmake")

foreach(f ${DATA_FILES})
    include(${f})
endforeach()

# Create the targets for all the components
foreach(_COMPONENT ${sdl_COMPONENT_NAMES} )
    if(NOT TARGET ${_COMPONENT})
        add_library(${_COMPONENT} INTERFACE IMPORTED)
        message(${SDL3_MESSAGE_MODE} "Conan: Component target declared '${_COMPONENT}'")
    endif()
endforeach()

if(NOT TARGET sdl::sdl)
    add_library(sdl::sdl INTERFACE IMPORTED)
    message(${SDL3_MESSAGE_MODE} "Conan: Target declared 'sdl::sdl'")
endif()
if(NOT TARGET SDL3::SDL3-shared)
    add_library(SDL3::SDL3-shared INTERFACE IMPORTED)
    set_property(TARGET SDL3::SDL3-shared PROPERTY INTERFACE_LINK_LIBRARIES SDL3::SDL3)
endif()
# Load the debug and release library finders
file(GLOB CONFIG_FILES "${CMAKE_CURRENT_LIST_DIR}/SDL3-Target-*.cmake")

foreach(f ${CONFIG_FILES})
    include(${f})
endforeach()