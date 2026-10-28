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

bool FlowExtractor::process_packet(const Packet& packet)
{
    std::string error_message;
    DecodedPacket decoded_packet;
    if (!decode_packet(packet, decoded_packet, error_message))
    {
        std::cerr << "Skipping packet: " << error_message << '\n';
        return false;
    }

    FlowKey flow_key {
        decoded_packet.source_ip,
        decoded_packet.destination_ip,
        decoded_packet.source_port,
        decoded_packet.destination_port,
        decoded_packet.vlan_ids,
        decoded_packet.protocol
    };

    constexpr std::chrono::seconds idle_timeout = std::chrono::seconds(30);

    auto given_flow = active_flows.find(flow_key);

    if (given_flow != active_flows.end() && decoded_packet.timestamp - given_flow->second.last_packet_time > idle_timeout)
    {
        Flow completed_flow = given_flow->second;
        completed_flow.duration = given_flow->second.last_packet_time - given_flow->second.first_packet_time;
        flows.push_back(completed_flow);
        active_flows.erase(given_flow);
        given_flow = active_flows.end();
    }
    if (given_flow != active_flows.end())
    {
        Flow& flow = given_flow->second;
        flow.last_packet_time = decoded_packet.timestamp;
        flow.packet_count++;
        flow.bytes_transferred += decoded_packet.packet_length;
        update_tcp_flag_counts(flow, decoded_packet);
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
        flow.vlan_ids = decoded_packet.vlan_ids;
        update_tcp_flag_counts(flow, decoded_packet);
        active_flows[flow_key] = flow;
    }

    return true;
}

std::vector<Flow> FlowExtractor::finish()
{
    for (auto& entry : active_flows)
    {
        Flow& flow = entry.second;
        flow.duration = flow.last_packet_time - flow.first_packet_time;
        flows.push_back(flow);
    }
    active_flows.clear();
    return flows;
}
