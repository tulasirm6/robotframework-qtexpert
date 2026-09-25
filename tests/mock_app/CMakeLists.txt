cmake_minimum_required(VERSION 3.10)
project(qt5_mock_app LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(Qt5 REQUIRED COMPONENTS Core Gui Widgets)

set(CMAKE_AUTOMOC ON)

add_executable(qt5_mock_app
    main.cpp
)

target_link_libraries(qt5_mock_app PRIVATE
    Qt5::Core
    Qt5::Gui
    Qt5::Widgets
)
