#ifndef NETGUARD_VALIDATE_LINK_H
#define NETGUARD_VALIDATE_LINK_H
#include <string>
#include <pcap/pcap.h>

bool validate_link_type(pcap_t* capture, std::string& error_message);

#endif //NETGUARD_VALIDATE_LINK_H