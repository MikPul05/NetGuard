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




## Running with Docker

The image builds the C++ importer and bundles it with the Python detection engine, so nothing (libpcap, RapidJSON, vcpkg, Python) has to be installed on the host.

```bash
# build the image
docker compose build

# put your capture in ./data, then run the whole pipeline (PCAP -> flows -> detections)
cp capture.pcap data/
docker compose run --rm netguard pipeline capture.pcap
# results: data/out/flows.jsonl and data/out/detections.jsonl
```

Individual steps:

```bash
docker compose run --rm netguard extract  capture.pcap flows.jsonl
docker compose run --rm netguard detect   flows.jsonl --out detections.jsonl
docker compose run --rm netguard evaluate flows.jsonl labels.csv
docker compose run --rm netguard demo      # engine on the bundled sample flows
docker compose run --rm netguard help
```

All paths are relative to `./data` (mounted as `/data` in the container). The bundled `detection_engine/config.toml` is used by default; to use your own, put it in `./data` and pass `--config config.toml`.

Without Compose:

```bash
docker build -t netguard .
docker run --rm -v "$PWD/data:/data" netguard pipeline capture.pcap
```

## Streaming with Kafka

`docker compose up` starts the message broker and the streaming part of the platform:

| Service | What it does |
|---|---|
| `kafka` | Apache Kafka 3.9 (KRaft, single node). Inside Docker: `kafka:9092`, from the host: `localhost:9094` |
| `kafka-init` | creates topics `flows` and `detections` (3 partitions each), then exits |
| `kafka-ui` | web UI for topics and messages: http://localhost:8080 |
| `detector` | consumes `flows`, runs the detection engine, publishes to `detections` and appends to `data/stream/detections.jsonl` |

```bash
docker compose up -d --build                         # start Kafka + detector
cp capture.pcap data/
docker compose run --rm netguard stream capture.pcap  # PCAP -> importer -> topic "flows"
docker compose logs -f detector                      # watch detections arrive
```

Other commands:

```bash
docker compose run --rm netguard publish flows.jsonl --rate 5000   # replay a flows file at 5000 flows/s
docker compose down        # stop everything (Kafka data is kept in a volume)
docker compose down -v     # stop and delete Kafka data
```

How the detector works: flows are kept in a sliding event-time buffer (180 s by default) and re-evaluated by the batch engine every 2 s. A detection is published only once its time window has closed (5 s grace period for late flows); when no new flows arrive for 5 s, remaining open windows are flushed. Detection IDs are deterministic UUIDs, so the same detection always gets the same ID.

Current limitations:
- Run a single `detector` instance for now. Flows are keyed by source IP, so with several instances each one would only see part of the traffic per destination (DoS rule).
- Offsets are committed after each run; after a restart the history buffer starts empty, so windows in progress at the time of the restart may be missed.
- The importer still writes JSONL first and `publish` sends it to Kafka; a native Kafka producer in C++ (librdkafka) can replace that step later.
