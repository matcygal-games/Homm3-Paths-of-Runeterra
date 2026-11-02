# Load the debug and release variables
file(GLOB DATA_FILES "${CMAKE_CURRENT_LIST_DIR}/luajit-*-data.cmake")

foreach(f ${DATA_FILES})
    include(${f})
endforeach()

# Create the targets for all the components
foreach(_COMPONENT ${luajit_COMPONENT_NAMES} )
    if(NOT TARGET ${_COMPONENT})
        add_library(${_COMPONENT} INTERFACE IMPORTED)
        message(${luajit_MESSAGE_MODE} "Conan: Component target declared '${_COMPONENT}'")
    endif()
endforeach()

if(NOT TARGET luajit::luajit)
    add_library(luajit::luajit INTERFACE IMPORTED)
    message(${luajit_MESSAGE_MODE} "Conan: Target declared 'luajit::luajit'")
endif()
# Load the debug and release library finders
file(GLOB CONFIG_FILES "${CMAKE_CURRENT_LIST_DIR}/luajit-Target-*.cmake")

foreach(f ${CONFIG_FILES})
    include(${f})
endforeach()