cmake_minimum_required(VERSION 4.0)
project(NetGuard)

set(CMAKE_CXX_STANDARD 14)

add_executable(NetGuard
        src/main.cpp
        include/pcap_importer/input_file.h
        src/pcap_importer/input_file.cpp)

find_path(PCAP_INCLUDE_DIR NAMES pcap/pcap.h REQUIRED)
find_library(PCAP_LIBRARY NAMES pcap REQUIRED)

target_include_directories(NetGuard PRIVATE ${PCAP_INCLUDE_DIR})
target_link_libraries(NetGuard PRIVATE ${PCAP_LIBRARY})