#include <iostream>
#include <string>
#include <pcap/pcap.h>

#include "../include/pcap_importer/input_file.h"
#include "../include/pcap_importer/packet_reader.h"

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

    PacketReadStatus status;
    Packet packet = {};
    std::size_t packet_count = 0;
    bool loop = true;
    while (loop)
    {
        status = read_next_packet(capture, packet, error_message);
        switch (status)
        {
            case PacketReadStatus::PacketRead:
                packet_count++;
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
    pcap_close(capture);
    return 0;
}
