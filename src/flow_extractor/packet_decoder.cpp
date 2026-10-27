#include "../../include/flow_extractor/packet_decoder.h"
#include "../../include/flow_extractor/decoded_packet.h"


bool extract_ethernet_type(const Packet& packet, std::uint16_t& ethernet_type, std::string& error_message)
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

bool decode_packet(const Packet& packet, DecodedPacket& decoded_packet, std::string& error_message)
{
    error_message.clear();
    if (packet.data.size() < 14)
    {
        error_message = "Packet too small";
        return false;
    }

    std::uint16_t ethernet_type;
    extract_ethernet_type(packet, ethernet_type, error_message);

    if (ethernet_type != 0x0800)
    {
        error_message = "Packet is not IPv4";
        return false;
    }
    if (packet.data.size() < 34)
    {
        error_message = "Packet too small for IPv4 header";
        return false;
    }



    unsigned char ip_version = packet.data[14] >> 4;
    if (ip_version != 4)
    {
        error_message = "Invalid IP version in IPv4 packet";
        return false;
    }

    std::size_t ipv4_header_length = (packet.data[14] & 0x0f) * 4;
    std::size_t transport_offset = 14 + ipv4_header_length;

    if (ipv4_header_length < 20 || packet.data.size() < 14 + ipv4_header_length)
    {
        error_message = "Packet too small for its IPv4 header";
        return false;
    }

    const std::uint16_t fragment_info = (static_cast<std::uint16_t>(packet.data[20]) << 8) | static_cast<std::uint16_t>(packet.data[21]);

    if ((fragment_info & 0x3FFF) != 0)
    {
        error_message = "Fragmented IPv4 packets are not supported";
        return false;
    }

    if (packet.data[23] != 6 && packet.data[23] != 17)
    {
        error_message = "Unsupported protocol";
        return false;
    }

    decoded_packet.source_ip =
        std::to_string(packet.data[26]) + "." +
            std::to_string(packet.data[27]) + "." +
                std::to_string(packet.data[28]) + "." +
                    std::to_string(packet.data[29]);

    decoded_packet.destination_ip =
        std::to_string(packet.data[30]) + "." +
            std::to_string(packet.data[31]) + "." +
                std::to_string(packet.data[32]) + "." +
                    std::to_string(packet.data[33]);

    decoded_packet.protocol = packet.data[23];



    const std::uint16_t ipv4_total_length = (static_cast<std::uint16_t>(packet.data[16]) << 8) | static_cast<std::uint16_t>(packet.data[17]);

    if (ipv4_total_length < ipv4_header_length)
    {
        error_message = "Invalid IPv4 total length";
        return false;
    }

    const std::size_t ip_payload_length = ipv4_total_length - ipv4_header_length;

    if (decoded_packet.protocol == 6)
    {
        if (ip_payload_length < 20 || packet.data.size() < transport_offset + 20)
        {
            error_message = "Packet too short for TCP header";
            return false;
        }

        const std::size_t tcp_header_length = (packet.data[transport_offset + 12] >> 4) * 4;

        if (tcp_header_length < 20 || ip_payload_length < tcp_header_length || packet.data.size() < transport_offset + tcp_header_length)
        {
            error_message = "Invalid or incomplete TCP header";
            return false;
        }

        decoded_packet.tcp_flags = packet.data[transport_offset + 13];
    }
    else
    {
        if (ip_payload_length < 8 || packet.data.size() < transport_offset + 8)
        {
            error_message = "Packet too short for UDP header";
            return false;
        }

        decoded_packet.tcp_flags = 0;
    }

    decoded_packet.source_port = static_cast<uint16_t>(packet.data[transport_offset] << 8 | packet.data[transport_offset + 1]);
    decoded_packet.destination_port = static_cast<uint16_t>(packet.data[transport_offset + 2] << 8 | packet.data[transport_offset + 3]);
    decoded_packet.timestamp = std::chrono::seconds(packet.header.ts.tv_sec) + std::chrono::microseconds(packet.header.ts.tv_usec);
    decoded_packet.packet_length = packet.header.len;


    return true;

}
