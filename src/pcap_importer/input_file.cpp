#include "../../include/pcap_importer/input_file.h"

pcap_t* open_capture_file(const std::string& path, std::string& error_message)
{
    char error_buffer[PCAP_ERRBUF_SIZE] = {};

    pcap_t* capture = pcap_open_offline(path.c_str(), error_buffer);

    if (capture == nullptr)
    {
        error_message = error_buffer;
        return nullptr;
    }

    return capture;
}