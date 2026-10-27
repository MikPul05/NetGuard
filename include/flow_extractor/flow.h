#ifndef NETGUARD_FLOW_H
#define NETGUARD_FLOW_H
#include <chrono>
#include <string>

//Custom struct for defining each flow.
struct Flow
{
    std::string destination_ip;
    std::string source_ip;
    std::uint16_t source_port = 0;
    std::uint16_t destination_port = 0;
    unsigned int protocol = 0;
    std::chrono::microseconds first_packet_time;
    std::chrono::microseconds last_packet_time;
    std::uint64_t packet_count = 0;
    std::uint64_t bytes_transferred = 0;
    std::uint64_t tcp_syn_count = 0;
    std::uint64_t tcp_ack_count = 0;
    std::uint64_t tcp_fin_count = 0;
    std::uint64_t tcp_rst_count = 0;
    std::chrono::microseconds duration;

};

// Key struct for Flow to use in an unordered map in flow_extractor::process_packet
struct FlowKey
{
    std::string source_ip;
    std::string destination_ip;
    std::uint16_t source_port;
    std::uint16_t destination_port;
    unsigned int protocol;

    bool operator==(const FlowKey& other) const
    {
        return source_ip == other.source_ip &&
            destination_ip == other.destination_ip &&
                source_port == other.source_port &&
                    destination_port == other.destination_port &&
                        protocol == other.protocol;
    }
};

//I lowkey found this on stack overflow
//This is necessary because unordered map does NOT know how to hash custom structs
//I have no idea what it does. The output is between God and the compiler :pray:
template <class T>
inline void hash_combine(std::size_t & s, const T & v)
{
    std::hash<T> hasher;
    s ^= hasher(v) + 0x9e3779b9 + (s << 6) + (s >> 2);
}

struct FlowKeyHash
{
    std::size_t operator()(const FlowKey& key) const
    {
        std::size_t seed = 0;
        hash_combine(seed, key.source_ip);
        hash_combine(seed, key.destination_ip);
        hash_combine(seed, key.source_port);
        hash_combine(seed, key.destination_port);
        hash_combine(seed, key.protocol);

        return seed;
    }

};

#endif //NETGUARD_FLOW_H