#ifndef NETGUARD_FLOW_EXTRACTOR_H
#define NETGUARD_FLOW_EXTRACTOR_H
#include <unordered_map>
#include <vector>
#include "flow.h"

struct Packet;

class FlowExtractor
{
    private:
        std::vector<Flow> flows;
        std::unordered_map<FlowKey, Flow, FlowKeyHash> active_flows;

    public:
        void process_packet(const Packet&);

        std::vector<Flow> finish();

};

#endif //NETGUARD_FLOW_EXTRACTOR_H