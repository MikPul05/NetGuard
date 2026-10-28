#include <iostream>
#include <string>
#include <pcap/pcap.h>
#include <fstream>

#include "../include/flow_extractor/flow_extractor.h"
#include "../include/pcap_importer/input_file.h"
#include "../include/pcap_importer/packet_reader.h"
#include "../include/pcap_importer/validate_link.h"
#include "../include/flow_extractor/packet_decoder.h"
#include "../include/flow_extractor/flow_serializer.h"

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
    std::size_t skipped_ipv4_packet_count = 0;
    std::uint16_t ethernet_type = 0;
    std::uint16_t ip_offset = 0;
    FlowExtractor flow_extractor;
    std::vector<std::uint16_t> vlan_ids;
    std::chrono::microseconds packet_time = std::chrono::microseconds::zero();
    bool loop = true;
    bool said = false;
    while (loop)
    {
        PacketReadStatus status = read_next_packet(capture, packet, error_message);
        switch (status)
        {
            case PacketReadStatus::PacketRead:
                packet_count++;
            const auto current_packet_time = std::chrono::seconds(packet.header.ts.tv_sec) + std::chrono::microseconds(packet.header.ts.tv_usec);

                if (current_packet_time < packet_time && said == false)
                {
                    std::cerr<<"Data in file is not chronological"<<'\n';
                    said = true;
                }
                packet_time = current_packet_time;

                if (!extract_ethernet_type(packet, ethernet_type, ip_offset, vlan_ids, error_message))
                {
                    malformed_packet_count++;
                    std::cerr<<"Skipping malformed packet: "<<packet_count<<":"<<error_message<<"\n";
                    break;
                }
                else if (ethernet_type == 0x0800) //IPv4
                {
                    ipv4_packet_count++;
                    if (!flow_extractor.process_packet(packet))
                    {
                        skipped_ipv4_packet_count++;
                    }
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


    std::vector<Flow> flows = flow_extractor.finish();

    std::string output_path;
    std::ofstream json_file(output_path);
    while (!json_file.is_open())
    {
        std::cout << "Enter the path for the JSONL output file: ";

        if (!std::getline(std::cin, output_path))
        {
            std::cerr << "No output path provided\n";
            pcap_close(capture);
            return 1;
        }

        json_file.clear();
        json_file.open(output_path);

        if (!json_file.is_open())
        {
            std::cerr << "Could not open that path. Try again.\n";
        }
    }

    for (const Flow& flow : flows)
    {
        json_file << serialize_flow_json(flow) << '\n';
    }

    json_file.close();
    if (!json_file)
    {
        std::cerr << "Error while writing the JSONL file\n";
        pcap_close(capture);
        return 1;
    }

    // std::cout<<"Packets read: "<<packet_count<<'\n';
    // std::cout<<"Malformed packets: "<<malformed_packet_count<<'\n';
    // std::cout<<"IPv4: "<<ipv4_packet_count<<'\n';
    // std::cout<<"IPv6: "<<ipv6_packet_count<<'\n';
    // std::cout<<"Skipped IPv4: "<<skipped_ipv4_packet_count<<'\n';
    // std::cout<<"Other packets: "<<other_packet_count<<'\n';
    // std::cout<<"Amount of flows captured: "<<flows.size()<<'\n';
    // for (const Flow& flow : flows)
    // {
    //     std::cout << flow.source_ip << ':' << flow.source_port
    //               << " -> " << flow.destination_ip << ':' << flow.destination_port
    //               << ", protocol: " << flow.protocol
    //               << ", first packet time (microseconds since Unix epoch): "
    //               << flow.first_packet_time.count()
    //               << ", packets: " << flow.packet_count
    //               << ", bytes: " << flow.bytes_transferred
    //               << ", duration (microseconds): " << flow.duration.count()
    //               << ", SYN: " << flow.tcp_syn_count
    //               << ", ACK: " << flow.tcp_ack_count
    //               << ", FIN: " << flow.tcp_fin_count
    //               << ", RST: " << flow.tcp_rst_count
    //               << '\n';
    // }

    pcap_close(capture);
    return 0;
}
