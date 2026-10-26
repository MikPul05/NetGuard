#ifndef NETGUARD_PACKET_READER_H
#define NETGUARD_PACKET_READER_H

#include <string>
#include <vector>
#include <pcap/pcap.h>

struct Packet
{
    struct pcap_pkthdr header;
    std::vector<unsigned char> data;
};

enum class PacketReadStatus
{
    EndOfFile,
    PacketRead,
    Error,
};

PacketReadStatus read_next_packet(pcap_t* capture, Packet& packet, std::string& error_message);


#endif //NETGUARD_PACKET_READER_H
