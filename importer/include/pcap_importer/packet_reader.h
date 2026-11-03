#ifndef NETGUARD_PACKET_READER_H
#define NETGUARD_PACKET_READER_H

#include <string>
#include <vector>
#include <pcap/pcap.h>

//pcap_pkthdr contains all the metadata of a packet
//data is a vector of u char (values range from 0 to 255), each index is the given byte and the data are the bits inside
struct Packet
{
    struct pcap_pkthdr header;
    std::vector<unsigned char> data;
};

//Easier way to handle statuses
enum class PacketReadStatus
{
    EndOfFile,
    PacketRead,
    Error
};

PacketReadStatus read_next_packet(pcap_t* capture, Packet& packet, std::string& error_message);


#endif //NETGUARD_PACKET_READER_H
