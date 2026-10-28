#include "../../include/flow_extractor/flow_serializer.h"
#include <rapidjson/writer.h>
#include <rapidjson/stringbuffer.h>

std::string serialize_flow_json(const Flow& flow)
{
    rapidjson::StringBuffer buffer;
    rapidjson::Writer<rapidjson::StringBuffer> writer(buffer);

    writer.StartObject();

    writer.Key("schema_version");
    writer.Uint(1);

    writer.Key("event_type");
    writer.String("netguard.normalized_flow");

    writer.Key("flow");
    writer.StartObject();

    writer.Key("source_ip");
    writer.String(flow.source_ip.c_str());

    writer.Key("destination_ip");
    writer.String(flow.destination_ip.c_str());

    writer.Key("source_port");
    writer.Uint(flow.source_port);

    writer.Key("destination_port");
    writer.Uint(flow.destination_port);

    writer.Key("protocol");
    writer.Uint(flow.protocol);

    writer.Key("start_time_unix_us");
    writer.Int64(static_cast<std::int64_t>(flow.first_packet_time.count()));

    writer.Key("duration_us");
    writer.Int64(static_cast<std::int64_t>(flow.duration.count()));

    writer.Key("packet_count");
    writer.Uint64(flow.packet_count);

    writer.Key("byte_count");
    writer.Uint64(flow.bytes_transferred);

    writer.Key("vlan_ids");
    writer.StartArray();
    for (const std::uint16_t vlan_id : flow.vlan_ids)
    {
        writer.Uint(vlan_id);
    }
    writer.EndArray();

    writer.Key("tcp_flag_counts");
    if (flow.protocol == 6)
    {
        writer.StartObject();

        writer.Key("syn");
        writer.Uint64(flow.tcp_syn_count);

        writer.Key("ack");
        writer.Uint64(flow.tcp_ack_count);

        writer.Key("fin");
        writer.Uint64(flow.tcp_fin_count);

        writer.Key("rst");
        writer.Uint64(flow.tcp_rst_count);

        writer.EndObject();
    }
    else
    {
        writer.Null();
    }

    writer.EndObject();
    writer.EndObject();

    return std::string(buffer.GetString(), buffer.GetSize());
}