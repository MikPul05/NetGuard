#include <iostream>
#include <string>
#include <pcap/pcap.h>

#include "../include/flow_extractor/flow_extractor.h"
#include "../include/pcap_importer/input_file.h"
#include "../include/pcap_importer/packet_reader.h"
#include "../include/pcap_importer/validate_link.h"
#include "../include/flow_extractor/packet_decoder.h"

int main()
{
    std::string path;
    std::cout << "Enter the path for the PCAP/PCAPNG file: ";
    std::getline(std::cin, path);
    std::string error_message;
    pcap_t* capture = open_capture_file(path, error_message);

    if (capture == nullptr)
    {
        std::cerr<<"Error while opening the file: "<<error_message<<'\n';
        return 1;
    }

    if (!validate_link_type(capture, error_message))
    {
        pcap_close(capture);
        std::cerr<<"Error while validating the file: "<<error_message<<'\n';
        return 1;
    }

    Packet packet = {};
    std::size_t packet_count = 0;
    std::size_t malformed_packet_count = 0;
    std::size_t ipv4_packet_count = 0;
    std::size_t ipv6_packet_count = 0;
    std::size_t other_packet_count = 0;
    std::uint16_t ethernet_type = 0;
    FlowExtractor flow_extractor;
    bool loop = true;
    while (loop)
    {
        PacketReadStatus status = read_next_packet(capture, packet, error_message);
        switch (status)
        {
            case PacketReadStatus::PacketRead:
                packet_count++;
                flow_extractor.process_packet(packet);
                if (!extract_ethernet_type(packet, ethernet_type, error_message))
                {
                    malformed_packet_count++;
                    std::cerr<<"Skipping malformed packet: "<<packet_count<<":"<<error_message<<"\n";
                    break;
                }
                else if (ethernet_type == 0x0800) //IPv4
                {
                    ipv4_packet_count++;
                }
                else if (ethernet_type == 0x86DD) //IPv6
                {
                    ipv6_packet_count++;
                }
                else
                {
                    other_packet_count++;
                }
                break;

            case PacketReadStatus::EndOfFile:
                loop = false;
                break;

            case PacketReadStatus::Error:
                std::cerr<<"Error while reading the file: "<<error_message<<'\n';
                pcap_close(capture);
                return 1;

            default:
                break;
        }
    }



    std::cout<<"Packets read: "<<packet_count<<'\n';
    std::cout<<"Malformed packets: "<<malformed_packet_count<<'\n';
    std::cout<<"IPv4: "<<ipv4_packet_count<<'\n';
    std::cout<<"IPv6: "<<ipv6_packet_count<<'\n';
    std::cout<<"Other packets: "<<other_packet_count<<'\n';


    pcap_close(capture);
    return 0;
}
