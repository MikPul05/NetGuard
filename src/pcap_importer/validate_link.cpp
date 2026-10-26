#include "../../include/pcap_importer/validate_link.h"

bool validate_link_type(pcap_t* capture, std::string& error_message)
{
    if (pcap_datalink(capture) == DLT_EN10MB)
    {
        return true;
    }
    else
    {
        error_message = "Unsupported link type :p";
        return false;
    }
}