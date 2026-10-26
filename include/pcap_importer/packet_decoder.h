#ifndef NETGUARD_PACKET_DECODER_H
#define NETGUARD_PACKET_DECODER_H
#include "packet_reader.h"
#include <string>

bool extract_ethernet_type(Packet &packet, std::uint16_t& ethernet_type, std::string& error_message);

#endif //NETGUARD_PACKET_DECODER_H