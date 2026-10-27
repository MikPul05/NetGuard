#include "../../include/flow_extractor/flow_extractor.h"

#include <iostream>

#include "../../include/flow_extractor/packet_decoder.h"
#include "../../include/flow_extractor/decoded_packet.h"

void FlowExtractor::process_packet(const Packet& packet)
{
    std::string error_message;
    DecodedPacket decoded_packet;
    if (!decode_packet(packet, decoded_packet, error_message))
    {
        std::cerr << "Skipping packet: " << error_message << '\n';
    }
}

std::vector<Flow> FlowExtractor::finish()
{
    return flows;
}
