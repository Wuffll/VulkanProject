cmake_minimum_required(VERSION 3.14...4.4)

set(LIB_NAME Logger)

set(INC_DIR "${CMAKE_SOURCE_DIR}/include")
set(LIB_INC_DIR "${INC_DIR}/${LIB_NAME}/include")
set(LIB_INC_DIR_PRIV "${LIB_INC_DIR}/${LIB_NAME}")

set(SOURCES
        Logger.cpp
)

add_library(${LIB_NAME} ${SOURCES})
target_include_directories(${LIB_NAME} PUBLIC "${LIB_INC_DIR}")
