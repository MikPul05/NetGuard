#include "../../include/pcap_importer/packet_decoder.h"

bool extract_ethernet_type(Packet& packet, std::uint16_t& ethernet_type, std::string& error_message)
{
    error_message.clear();

    if (packet.data.size() < 14)
    {
        error_message = "Packet too small";
        return false;
    }


    ethernet_type = (packet.data[12] <<8 ) | packet.data[13];
    return true;
}
