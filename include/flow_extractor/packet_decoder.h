#ifndef NETGUARD_PACKET_DECODER_H
#define NETGUARD_PACKET_DECODER_H

#include "../pcap_importer/packet_reader.h"
#include <string>
#include "decoded_packet.h"

bool extract_ethernet_type(const Packet&, std::uint16_t&, std::string&);

bool decode_packet(const Packet&, DecodedPacket&, std::string&);

#endif //NETGUARD_PACKET_DECODER_H