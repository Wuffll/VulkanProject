cmake_minimum_required(VERSION 3.14...4.4)

set(INC_DIR "${CMAKE_SOURCE_DIR}/include")
set(LIB_INC_DIR "${INC_DIR}/DummyLibrary/include")
set(LIB_INC_DIR_PRIV "${LIB_INC_DIR}/DummyLibrary")

set(SOURCES
        DummyLibrary.cpp
)

add_library(DummyLibrary ${SOURCES})
target_include_directories(DummyLibrary PUBLIC "${LIB_INC_DIR}")