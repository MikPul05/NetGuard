### We currently have:
- reading PCAP and PCAPNG files
- identifying Ethernet frame type from EtherType
- validation of headers for Ethernet, IPv4, TCP, UDP
- packet grouping into directional flows
- normalizing flow data
- VLAN handling


### What we still need to implement:
- IPv6 decoding and grouping
- Handling of fragmented IPv4 packets


### JSONL output format

The program currently outputs a JSONL file with the following structure
```json
{
  "schema_version": 1,
  "event_type": "netguard.normalized_flow",
  "flow": {
    "source_ip": "111.111.111.111",
    "destination_ip": "111.111.111.111",
    "source_port": 10,
    "destination_port": 20,
    "protocol": 6,
    "start_time_unix_us": 10,
    "duration_us": 10,
    "packet_count": 10,
    "byte_count": 10,
    "vlan_ids": [10, 20],
    "tcp_flag_counts": {
      "syn": 0,
      "ack": 0,
      "fin": 0,
      "rst": 0
    }
  }
}
```


- schema_version -  Version of the JSON data contract. The current version is 1. If the structure changes a lot we can still keep the old processing logic and just add new one for schema_version = 2 
- event_type - just in case if we want check/categorize for event types, we can get rid of it 
-  source_ip, destination_ip - Source and destination IP addresses for this direction of the flow. The reverse direction is a separate flow 
- source_port, destination_port - Source and destination ports
- protocol - IP protocol number: 6 for TCP and 17 for UDP
- start_time_unix_us - Timestamp of the first packet, in microseconds since the Unix epoch
- duration_us - Flow duration in microseconds
- packet_count - Number of packets included in the flow
- byte_count - Sum of IPv4 packet lengths, including IPv4 headers but excluding Ethernet and VLAN headers
- vlan_ids - VLAN IDs in outer-to-inner tag order. An untagged packet has an empty list 
- tcp_flag_counts - For TCP, counts packets that contain each listed flag. A packet may increment more than one count. We can add more flags if needed. For UDP, this field is null

New fields can be easily added while keeping existing field names, types, and units unchanged \
You can ignore the fields that you dont need \
Changes that break compatibility, like i said, will require a new schema_version



