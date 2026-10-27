#ifndef NETGUARD_FLOW_H
#define NETGUARD_FLOW_H
#include <chrono>
#include <string>

struct Flow
{
    std::string destination_ip;
    std::string source_ip;
    std::uint16_t source_port = 0;
    std::uint16_t destination_port = 0;
    unsigned int protocol = 0;
    std::chrono::microseconds first_packet_time;
    std::chrono::microseconds last_packet_time;
    std::uint64_t packet_count = 0;
    std::uint64_t bytes_transferred = 0;
    std::uint8_t tcp_flags;

};

#endif //NETGUARD_FLOW_H