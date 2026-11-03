cmake_minimum_required(VERSION 3.16...4.0)
project(NetGuard)

set(CMAKE_CXX_STANDARD 14)

add_executable(NetGuard
        importer/src/main.cpp
        importer/include/pcap_importer/input_file.h
        importer/src/pcap_importer/input_file.cpp
        importer/include/pcap_importer/packet_reader.h
        importer/src/pcap_importer/packet_reader.cpp
        importer/include/pcap_importer/validate_link.h
        importer/src/pcap_importer/validate_link.cpp
        importer/include/flow_extractor/packet_decoder.h
        importer/src/flow_extractor/packet_decoder.cpp
        importer/include/flow_extractor/flow.h
        importer/include/flow_extractor/flow_extractor.h
        importer/src/flow_extractor/flow_extractor.cpp
        importer/include/flow_extractor/decoded_packet.h
        importer/include/flow_extractor/flow_serializer.h
        importer/src/flow_extractor/flow_serializer.cpp)

find_path(PCAP_INCLUDE_DIR NAMES pcap/pcap.h REQUIRED)
find_library(PCAP_LIBRARY NAMES pcap REQUIRED)

target_include_directories(NetGuard PRIVATE ${PCAP_INCLUDE_DIR})
target_link_libraries(NetGuard PRIVATE ${PCAP_LIBRARY})

find_package(RapidJSON CONFIG REQUIRED)
# vcpkg / newer RapidJSON export an imported target; the Debian/Ubuntu package
# (1.1.0) only sets include-dir variables, so fall back to those.
if(TARGET rapidjson)
    target_link_libraries(NetGuard PRIVATE rapidjson)
elseif(TARGET RapidJSON)
    target_link_libraries(NetGuard PRIVATE RapidJSON)
endif()
target_include_directories(NetGuard PRIVATE ${PCAP_INCLUDE_DIR} ${RAPIDJSON_INCLUDE_DIRS} ${RapidJSON_INCLUDE_DIRS})

install(TARGETS NetGuard RUNTIME DESTINATION bin)
