#include "../../include/pcap_importer/packet_reader.h"

PacketReadStatus read_next_packet(pcap_t* capture, Packet& packet, std::string& error_message)
{
    error_message.clear();

    struct pcap_pkthdr* header = nullptr;
    const u_char* packet_data = nullptr;

    //https://www.tcpdump.org/manpages/pcap_next_ex.3pcap.html
    const int result = pcap_next_ex(capture, &header, &packet_data);

    switch (result)
    {
        case -1:
            error_message = pcap_geterr(capture);
            return PacketReadStatus::Error;


        case -2:
            return PacketReadStatus::EndOfFile;


        case 1:
            packet.header = *header;
            if (header->caplen > 0)
            {
                packet.data.assign(packet_data, packet_data + header->caplen);
            }
            else
            {
                packet.data.clear();
            }
            return PacketReadStatus::PacketRead;


        default:
            break;
    }

    error_message = "Unknown error";
    return PacketReadStatus::Error;
}