cmake_minimum_required(VERSION 3.14...4.4)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Project definition
project(VulkanProject
        VERSION 0.0.1
        DESCRIPTION "Reintroduction to Vulkan"
        LANGUAGES CXX)

# Set source directory
set(SRC_DIR "${CMAKE_CURRENT_SOURCE_DIR}/src")

# Set CMake module directory
list(APPEND CMAKE_MODULE_PATH "${CMAKE_SOURCE_DIR}/cmake")

# Add/check for requirements
include(AddAssimp)
find_package(Vulkan REQUIRED)

add_subdirectory(src)