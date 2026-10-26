#include <iostream>
#include <string>
#include "pcap_importer/input_file.h"

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
        return 0;
    }

    std::cout<<"File opened!\n";




    pcap_close(capture);
    return 0;
}