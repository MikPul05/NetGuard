
#ifndef NETGUARD_INPUT_FILE_H
#define NETGUARD_INPUT_FILE_H

#include <pcap/pcap.h>
#include <string>

pcap_t* open_capture_file(const std::string& path, std::string& error);

#endif //NETGUARD_INPUT_FILE_H

