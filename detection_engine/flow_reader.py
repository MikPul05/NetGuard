import json

SUPPORTED_SCHEMA_VERSION = 1
TCP = 6
UDP = 17
def read_flows(path):
   
    flows = []
    bad_lines = 0

    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                bad_lines += 1
                continue

            if event.get("schema_version") != SUPPORTED_SCHEMA_VERSION or "flow" not in event:
                bad_lines += 1
                continue

            flows.append(event["flow"])

    flows.sort(key=lambda flow: flow["start_time_unix_us"])
    return flows, bad_lines

def is_connection_attempt(flow):
    
    if flow["protocol"] == UDP:
        return True
    if flow["protocol"] != TCP:
        return False

    flags = flow.get("tcp_flag_counts") or {}
    syn = flags.get("syn", 0)
    ack = flags.get("ack", 0)
    return syn >= 1 and ack < flow["packet_count"]