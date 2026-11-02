# Load the debug and release variables
file(GLOB DATA_FILES "${CMAKE_CURRENT_LIST_DIR}/plutosvg-*-data.cmake")

foreach(f ${DATA_FILES})
    include(${f})
endforeach()

# Create the targets for all the components
foreach(_COMPONENT ${plutosvg_COMPONENT_NAMES} )
    if(NOT TARGET ${_COMPONENT})
        add_library(${_COMPONENT} INTERFACE IMPORTED)
        message(${plutosvg_MESSAGE_MODE} "Conan: Component target declared '${_COMPONENT}'")
    endif()
endforeach()

if(NOT TARGET plutosvg::plutosvg)
    add_library(plutosvg::plutosvg INTERFACE IMPORTED)
    message(${plutosvg_MESSAGE_MODE} "Conan: Target declared 'plutosvg::plutosvg'")
endif()
# Load the debug and release library finders
file(GLOB CONFIG_FILES "${CMAKE_CURRENT_LIST_DIR}/plutosvg-Target-*.cmake")

foreach(f ${CONFIG_FILES})
    include(${f})
endforeach()