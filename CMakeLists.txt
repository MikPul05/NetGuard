cmake_minimum_required(VERSION 4.0)
project(NetGuard)

set(CMAKE_CXX_STANDARD 14)

add_executable(NetGuard
        src/main.cpp
        include/pcap_importer/input_file.h
        src/pcap_importer/input_file.cpp
        include/pcap_importer/packet_reader.h
        src/pcap_importer/packet_reader.cpp
        include/pcap_importer/validate_link.h
        src/pcap_importer/validate_link.cpp
        include/flow_extractor/packet_decoder.h
        src/flow_extractor/packet_decoder.cpp
        include/flow_extractor/flow.h
        include/flow_extractor/flow_extractor.h
        src/flow_extractor/flow_extractor.cpp
        include/flow_extractor/decoded_packet.h)

find_path(PCAP_INCLUDE_DIR NAMES pcap/pcap.h REQUIRED)
find_library(PCAP_LIBRARY NAMES pcap REQUIRED)

target_include_directories(NetGuard PRIVATE ${PCAP_INCLUDE_DIR})
target_link_libraries(NetGuard PRIVATE ${PCAP_LIBRARY})