#include "../../include/flow_extractor/packet_decoder.h"
#include "../../include/flow_extractor/decoded_packet.h"

std::string format_ipv6_address(const Packet& packet, std::size_t offset)
{
    const char* hex_digits = "0123456789abcdef";
    std::string address;
    address.reserve(39);

    for (std::size_t group = 0; group < 8; ++group)
    {
        if (group > 0)
        {
            address += ':';
        }

        const unsigned int value =
            (static_cast<unsigned int>(packet.data[offset + group * 2]) << 8) |
            static_cast<unsigned int>(packet.data[offset + group * 2 + 1]);

        address += hex_digits[(value >> 12) & 0x0F];
        address += hex_digits[(value >> 8) & 0x0F];
        address += hex_digits[(value >> 4) & 0x0F];
        address += hex_digits[value & 0x0F];
    }

    return address;
}

bool extract_ethernet_type(const Packet& packet, std::uint16_t& ethernet_type, std::uint16_t& ip_offset, std::vector<std::uint16_t>& vlan_ids, std::string& error_message)
{
    vlan_ids.clear();
    error_message.clear();
    //Ethernet header has 14 bytes
    //if < 14 bytes, then we can not read the EtherType field
    if (packet.data.size() < 14)
    {
        error_message = "Packet too small";
        return false;
    }
    //Ethernet Type is located in the 13th and 14th byte of the ethernet header
    ethernet_type = (packet.data[12] <<8 ) | packet.data[13];
    ip_offset = 14;
    std::size_t type_offset = 12;
    ethernet_type = (static_cast<std::uint16_t>(packet.data[type_offset]) << 8) | packet.data[type_offset + 1];

    while (ethernet_type == 0x8100 || ethernet_type == 0x88A8)
    {
        // We check if VLAN tag and following EtherType are present
        //https://en.wikipedia.org/wiki/IEEE_802.1Q
        if (packet.data.size() < type_offset + 6)
        {
            error_message = "VLAN tagged Ethernet frame is too short";
            return false;
        }

        const std::uint16_t tci = (static_cast<std::uint16_t>(packet.data[type_offset + 2]) << 8) |packet.data[type_offset + 3];

        vlan_ids.push_back(tci & 0x0FFF);
        type_offset += 4;
        ethernet_type = (static_cast<std::uint16_t>(packet.data[type_offset]) << 8) | packet.data[type_offset + 1];
    }

    ip_offset = type_offset + 2;
    return true;
}




bool decode_packet(const Packet& packet, DecodedPacket& decoded_packet, std::string& error_message)
{
    error_message.clear();
    //Ethernet header has 14 bytes
    //if < 14 bytes, then we can not read the EtherType field
    if (packet.data.size() < 14)
    {
        error_message = "Packet too small";
        return false;
    }

    std::uint16_t ethernet_type;
    std::uint16_t ip_offset;
    unsigned char ip_version;
    std::size_t transport_offset;
    std::size_t ip_payload_length;
    std::size_t ip_total_length;
    if (!extract_ethernet_type(packet, ethernet_type, ip_offset, decoded_packet.vlan_ids, error_message)) return false;

    //0x0800 is IPv4
    //0x86DD is IPv6
    if (ethernet_type == 0x0800)
    {
        //Ethernet is 14 bytes + minimal IPv4 header which is 20 bytes
        if (packet.data.size() < ip_offset + 20)
        {
            error_message = "Packet too small for IPv4 header";
            return false;
        }
        //First 4 bits of the 15th byte have the ip version (first byte of the IPv4 header, since ethernet is 14bytes, and its first)
        //4 is for Ipv4
        ip_version = packet.data[ip_offset] >> 4;
        if (ip_version != 4)
        {
            error_message = "Invalid IP version in IPv4 packet";
            return false;
        }

        //The last 4 bits of the 15th byte (First field in the IPv4 header) tell us the length of the IPv4 header (min 20 bytes, max 60bytes)
        std::size_t ipv4_header_length = (packet.data[ip_offset] & 0x0f) * 4;

        //transport offset is the place after Ethernet and IPv4 header
        transport_offset = ip_offset + ipv4_header_length;

        //IPv4 header can not be smaller than 20 bytes AND we check if all of its bytes have been saved to packet.data
        //14 bytes from Ethernet + ipv4 header length
        if (ipv4_header_length < 20 || packet.data.size() < transport_offset)
        {
            error_message = "Packet too small for its IPv4 header";
            return false;
        }

        //Bytes 21 and 22 (IPv4 Flags, IPv4 7th and 8th byte) contain the fragmentation flags and fragment offest
        const std::uint16_t fragment_info = (static_cast<std::uint16_t>(packet.data[ip_offset + 6]) << 8) | static_cast<std::uint16_t>(packet.data[ip_offset + 7]);

        //we throw out fragmented frames for now
        if ((fragment_info & 0x3FFF) != 0)
        {
            error_message = "Fragmented IPv4 packets are not supported";
            return false;
        }

        //Protocol field is the 10th byte of the IPv4 header (+ 14 bytes from ethernet, so its index in data is 23, since we count from 0)
        //here we check if its TCP (6) or UDP (17)
        if (packet.data[ip_offset + 9] != 6 && packet.data[ip_offset + 9] != 17)
        {
            error_message = "Unsupported protocol";
            return false;
        }

        //IPv4 addresses are always in these positions in the header
        decoded_packet.source_ip =
            std::to_string(packet.data[ip_offset + 12]) + "." +
                std::to_string(packet.data[ip_offset + 13]) + "." +
                    std::to_string(packet.data[ip_offset + 14]) + "." +
                        std::to_string(packet.data[ip_offset + 15]);

        decoded_packet.destination_ip =
            std::to_string(packet.data[ip_offset + 16]) + "." +
                std::to_string(packet.data[ip_offset + 17]) + "." +
                    std::to_string(packet.data[ip_offset + 18]) + "." +
                        std::to_string(packet.data[ip_offset + 19]);

        decoded_packet.protocol = packet.data[ip_offset + 9];


        //The total length of the IP packet is encoded in the 17th and 18th byte
        ip_total_length = (static_cast<std::uint16_t>(packet.data[ip_offset+2] << 8)) | static_cast<std::uint16_t>(packet.data[ip_offset+3]);

        //The whole IP packet HAS to be at least the size of the header, otherwise its invalid
        if (ip_total_length < ipv4_header_length)
        {
            error_message = "Invalid IPv4 total length";
            return false;
        }
        //check if the whole IPv4 packet fits in the data read from the file
        if (packet.data.size() < ip_offset + ip_total_length)
        {
            error_message = "Truncated IPv4 packet";
            return false;
        }

        //Amount of bytes after the IPv4 header, so its where TCP or UDP is
        ip_payload_length = ip_total_length - ipv4_header_length;

    }
    else if (ethernet_type == 0x86DD)
    {
        if (packet.data.size() < ip_offset + 40)
        {
            error_message = "Packet too small for IPv6 header";
            return false;
        }
        ip_version = packet.data[ip_offset] >> 4;
        if (ip_version != 6)
        {
            error_message = "Invalid IPv6 version";
            return false;
        }

        transport_offset = ip_offset + 40;

        if (packet.data.size() < transport_offset)
        {
            error_message = "Packet too small for its IPv6 header";
            return false;
        }

        const std::uint8_t dscp = (packet.data[ip_offset] & 0x0F)<<2 | (packet.data[ip_offset+1] & 0xC0) >> 6;
        const std::uint8_t ecn = (packet.data[ip_offset+1] & 0x30) >> 4;

        const std::uint32_t flow_label = (packet.data[ip_offset+1] & 0x0F)<<16 | packet.data[ip_offset+2]<<8 | packet.data[ip_offset+3];

        ip_payload_length = packet.data[ip_offset+4]<<8 | packet.data[ip_offset+5];
        ip_total_length = 40 + ip_payload_length;
        if (packet.data.size() < 40+ ip_payload_length + ip_offset)
        {
            error_message = "Truncated IPv6 packet";
            return false;
        }

        std::uint8_t next_header = packet.data[ip_offset + 6];
        std::size_t current_offset = ip_offset + 40;
        std::size_t remaining_payload = ip_payload_length;
        while (next_header != 6 && next_header != 17)
        {
            if (next_header == 44)
            {
                error_message = "IPv6 Fragment Header is not supported";
                return false;
            }

            if (next_header == 0 || next_header == 43 || next_header == 60)
            {
                if (remaining_payload < 2)
                {
                    error_message = "Truncated IPv6 extension header";
                    return false;
                }
                const std::size_t extension_length = (static_cast<std::size_t>(packet.data[current_offset + 1]) + 1) * 8;
                if (extension_length > remaining_payload)
                {
                    error_message = "Invalid IPv6 extension header length";
                    return false;
                }
                next_header = packet.data[current_offset];
                current_offset += extension_length;
                remaining_payload -= extension_length;
                continue;
            }
            if (next_header == 51)
            {
                if (remaining_payload < 2)
                {
                    error_message = "Truncated IPv6 authentication header";
                    return false;
                }
                const std::size_t extension_length = (static_cast<std::size_t>(packet.data[current_offset + 1]) + 2) * 4;

                if (extension_length > remaining_payload)
                {
                    error_message = "Invalid IPv6 Authentication Header length";
                    return false;
                }

                next_header = packet.data[current_offset];
                current_offset += extension_length;
                remaining_payload -= extension_length;
                continue;
            }

            error_message = "Unsupported IPv6 Next Header";
            return false;
        }

        decoded_packet.protocol = next_header;
        transport_offset = current_offset;
        ip_payload_length = remaining_payload;

        decoded_packet.source_ip = format_ipv6_address(packet, ip_offset + 8);
        decoded_packet.destination_ip = format_ipv6_address(packet, ip_offset + 24);

    }
    else
    {
        error_message = "Packet is not IPv4 or IPv6";
        return false;
    }

    if (decoded_packet.protocol == 6)
    {
        //Minimal TCP header has 20 bytes, and we check the declared size of the IP and the actual bytes in the buffer (data)
        if (ip_payload_length < 20 || packet.data.size() < transport_offset + 20)
            {
                error_message = "Packet too short for TCP header";
                return false;
            }

            //The length of the TCP header is in the first 4 bits of the 13th byte of the header
            //Given value means groups of 4 bytes
            const std::size_t tcp_header_length = (packet.data[transport_offset + 12] >> 4) * 4;

            //check if TCP header fits inside the IPv4 payload
            if (tcp_header_length > ip_payload_length)
            {
                error_message = "TCP header is longer than the IPv4 payload";
                return false;
            }

            //TCP header is at least 20 bytes and length of IP and available data must be the whole TCP header
            if (tcp_header_length < 20 || ip_payload_length < tcp_header_length || packet.data.size() < transport_offset + tcp_header_length)
            {
                error_message = "Invalid or incomplete TCP header";
                return false;
            }
            //TCP flags are in the 14th byte from the start of the header
            decoded_packet.tcp_flags = packet.data[transport_offset + 13];
    }
    else
    {
        //This is the UDP branch
        //UDP header has 8 bytes, we check the length of IP and available data
        if (ip_payload_length < 8 || packet.data.size() < transport_offset + 8)
        {
            error_message = "Packet too short for UDP header";
            return false;
        }

        //UDP header is always 8 bytes, so we calculate the whole UDP length
        const std::uint16_t udp_length =
            (static_cast<std::uint16_t>(packet.data[transport_offset + 4] << 8)) |
                (static_cast<std::uint16_t>(packet.data[transport_offset + 5]));

        //if less than 8 then its invalid, since header must have 8 bytes
        //UDP length must not exceed the IPv4 payload length
        if (udp_length < 8 || udp_length > ip_payload_length)
        {
            error_message = "Invalid UDP length";
            return false;
        }

        //UDP has no TCP flags
        decoded_packet.tcp_flags = 0;
    }

        //Ports info is at the beginning of both UDP and TCP header
        //Ports have 2 bytes each, first two for the source and the second two for the destination
        decoded_packet.source_port = static_cast<uint16_t>(packet.data[transport_offset] << 8 | packet.data[transport_offset + 1]);
        decoded_packet.destination_port = static_cast<uint16_t>(packet.data[transport_offset + 2] << 8 | packet.data[transport_offset + 3]);

        //Time of the packet saved as seconds and microseconds
        decoded_packet.timestamp = std::chrono::seconds(packet.header.ts.tv_sec) + std::chrono::microseconds(packet.header.ts.tv_usec);

        //IPv4 packet length including its header
        decoded_packet.packet_length = ip_total_length;

    return true;

}
