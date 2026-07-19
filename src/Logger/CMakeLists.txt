cmake_minimum_required(VERSION 3.14...4.4)

set(INC_DIR "${CMAKE_SOURCE_DIR}/include")
set(LIB_INC_DIR "${INC_DIR}/Logger/include")
set(LIB_INC_DIR_PRIV "${LIB_INC_DIR}/Logger")

set(SOURCES
        Logger.cpp
)

add_library(Logger ${SOURCES})
target_include_directories(Logger PUBLIC "${LIB_INC_DIR}")