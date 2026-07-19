cmake_minimum_required(VERSION 3.14...4.4)

add_subdirectory(DummyLibrary)
add_subdirectory(Logger)

set(MAIN_DIR ${CMAKE_SOURCE_DIR}/src/Main)

set(PROJECT_EXEC_NAME "VulkanApp")

set(EXTERNAL_DEPS_DIR ${CMAKE_BINARY_DIR}/_deps)
set(EXTERNAL_INCLUDES
        ${EXTERNAL_DEPS_DIR}/assimp-src/include
)

add_executable(${PROJECT_EXEC_NAME}
        ${MAIN_DIR}/main.cpp
)

set(LIBRARIES DummyLibrary Logger assimp vulkan)

target_link_libraries(${PROJECT_EXEC_NAME} PRIVATE ${LIBRARIES})
target_include_directories(${PROJECT_EXEC_NAME} PRIVATE ${EXTERNAL_INCLUDES})
