#ifndef NETGUARD_FLOW_SERIALIZER_H
#define NETGUARD_FLOW_SERIALIZER_H
#include "flow.h"

std::string serialize_flow_json(const Flow& flow);

#endif //NETGUARD_FLOW_SERIALIZER_H