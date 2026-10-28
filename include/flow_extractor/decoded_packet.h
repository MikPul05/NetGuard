#ifndef NETGUARD_DECODED_PACKET_H
#define NETGUARD_DECODED_PACKET_H
#include <chrono>
#include <string>

//Struct for a decoded packet
struct DecodedPacket
{
    std::string destination_ip;
    std::string source_ip;
    std::uint16_t source_port;
    std::uint16_t destination_port;
    unsigned int protocol;
    std::chrono::microseconds timestamp;
    std::size_t packet_length;
    std::uint8_t tcp_flags;
    std::vector<std::uint16_t> vlan_ids;
};

#endif //NETGUARD_DECODED_PACKET_H