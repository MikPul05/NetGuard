#include "../../include/flow_extractor/flow_extractor.h"

#include <iostream>

#include "../../include/flow_extractor/packet_decoder.h"
#include "../../include/flow_extractor/decoded_packet.h"

void update_tcp_flag_counts(Flow& flow, const DecodedPacket& packet)
{
    if (packet.protocol != 6)
    {
        return; // UDP nie ma flag TCP
    }

    if ((packet.tcp_flags & 0x02) != 0) ++flow.tcp_syn_count;
    if ((packet.tcp_flags & 0x10) != 0) ++flow.tcp_ack_count;
    if ((packet.tcp_flags & 0x01) != 0) ++flow.tcp_fin_count;
    if ((packet.tcp_flags & 0x04) != 0) ++flow.tcp_rst_count;
}

void FlowExtractor::process_packet(const Packet& packet)
{
    std::string error_message;
    DecodedPacket decoded_packet;
    if (!decode_packet(packet, decoded_packet, error_message))
    {
        std::cerr << "Skipping packet: " << error_message << '\n';
        return;
    }

    FlowKey flow_key {
        decoded_packet.source_ip,
        decoded_packet.destination_ip,
        decoded_packet.source_port,
        decoded_packet.destination_port,
        decoded_packet.protocol
    };

    if (active_flows.find(flow_key) != active_flows.end())
    {
        active_flows[flow_key].last_packet_time = decoded_packet.timestamp;
        active_flows[flow_key].packet_count++;
        active_flows[flow_key].bytes_transferred += decoded_packet.packet_length;
        update_tcp_flag_counts(active_flows[flow_key], decoded_packet);
    }
    else
    {
        Flow flow{};
        flow.destination_ip = decoded_packet.destination_ip;
        flow.source_ip = decoded_packet.source_ip;
        flow.source_port = decoded_packet.source_port;
        flow.destination_port = decoded_packet.destination_port;
        flow.protocol = decoded_packet.protocol;
        flow.first_packet_time = decoded_packet.timestamp;
        flow.last_packet_time = decoded_packet.timestamp;
        flow.packet_count = 1;
        flow.bytes_transferred = decoded_packet.packet_length;
        update_tcp_flag_counts(flow, decoded_packet);
        active_flows[flow_key] = flow;
    }
}

std::vector<Flow> FlowExtractor::finish()
{
    flows.clear();
    for (auto& entry : active_flows)
    {
        Flow& flow = entry.second;
        flow.duration = flow.last_packet_time - flow.first_packet_time;
        flows.push_back(flow);
    }
    return flows;
}
