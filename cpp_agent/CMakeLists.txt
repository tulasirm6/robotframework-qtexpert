cmake_minimum_required(VERSION 3.10)
project(qt_test_agent LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
set(CMAKE_AUTOMOC ON)

# Find Qt5 modules
find_package(Qt5 REQUIRED COMPONENTS Core Gui Widgets Network Test)

# Source files
set(AGENT_SOURCES
    src/agent.cpp
    src/agent.h
)

# Build shared library for LD_PRELOAD
add_library(qt_test_agent SHARED ${AGENT_SOURCES})

target_include_directories(qt_test_agent PRIVATE
    src
)

target_link_libraries(qt_test_agent PRIVATE
    Qt5::Core
    Qt5::Gui
    Qt5::Widgets
    Qt5::Network
    Qt5::Test
)

# Set library output properties
set_target_properties(qt_test_agent PROPERTIES
    OUTPUT_NAME "qt_test_agent"
    PREFIX "lib"
)
