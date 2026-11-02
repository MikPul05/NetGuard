### Current Implementation:
- reading PCAP and PCAPNG files
- support for Ethernet frames with stacked VLAN tags, including 802.1Q and QinQ
- identifying IPv4 and IPv6 packets from EtherType
- validation of headers for Ethernet, IPv4, IPv6, TCP, UDP and ICMPv6
- packet grouping into directional flows, with keeping VLAN IDs and ICMPv6 message details 
- normalizing flow data
- writing the normalized flows as JSONL, with one JSON object per line


### Current Limitations:
- Handling of fragmented IPv4 and IPv6 packets
- IPv6 packets with unsupported header values are skipped
- ICMPv6 validation is limited to the common header and the additional fields currently decoded for Echo Request and Echo Reply messages

### JSONL output format

The program currently outputs a JSONL file with the following structures

#### Example TCP flow:
```json
{
  "schema_version": 1,
  "event_type": "netguard.normalized_flow",
  "flow": {
    "source_ip": "192.168.1.10",
    "destination_ip": "203.0.113.20",
    "source_port": 51514,
    "destination_port": 443,
    "protocol": 6,
    "start_time_unix_us": 1760000000000000,
    "duration_us": 250000,
    "packet_count": 10,
    "byte_count": 6400,
    "vlan_ids": [],
    "icmpv6": null,
    "tcp_flag_counts": {
      "syn": 1,
      "ack": 8,
      "fin": 1,
      "rst": 0
    }
  }
}
```



- schema_version -  Version of the JSON data contract. The current version is 1. Adding new optional fields is okay for the same version. Changing the structure making it backwards incompatible requires new incremented version
- event_type - identification of the type of record. Just in case if we want check/categorize for event types
- source_ip, destination_ip - Source and destination IP addresses for this direction of the flow. The reverse direction is a separate flow 
- source_port, destination_port - Source and destination ports for TCP and UDP, ICMPv6 doesnt have ports, therefore they are 0s
- protocol - IP protocol number: 6 for TCP, 17 for UDP and 58 for ICMPv6
- start_time_unix_us - Timestamp of the first packet, in microseconds since the Unix epoch
- duration_us - Flow duration in microseconds
- packet_count - Number of packets included in the flow
- byte_count - Sum of IP packet lengths, including IP headers and IPv6 extension headers, but excluding Ethernet and VLAN headers
- vlan_ids - VLAN IDs in outer-to-inner tag order. An untagged packet has an empty list 
- icmpv6 - Present for ICMPv6 flows. Contains `type` and `code`. `identifier` is present for Echo request and reply and is NULL for other message types. Otherwise `icmpv6` is null.
- tcp_flag_counts - For TCP, counts packets that contain each listed flag. A packet may increment more than one count. We can add more flags if needed. For UDP or ICMPv6, this field is null

New fields can be easily added while keeping existing field names, types, and units unchanged \
You can ignore the fields that you dont need \
Changes that break compatibility, like i said, will require a new schema_version



