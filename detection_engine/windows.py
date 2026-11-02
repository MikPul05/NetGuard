from flow_reader import is_connection_attempt

US_PER_SECOND = 1_000_000


def window_start(time_us, window_seconds):
    size_us = window_seconds * US_PER_SECOND
    return (time_us // size_us) * size_us
def build_source_windows(flows, window_seconds):
    groups = {}
    for flow in flows:
        if not is_connection_attempt(flow):
            continue
        key = (flow["source_ip"], window_start(flow["start_time_unix_us"], window_seconds))
        w = groups.setdefault(key, {
            "attempts": 0, "dst_ports": set(), "dst_ips": set(),
            "service_attempts": {}, "bytes": 0,
        })
        w["attempts"] += 1
        w["dst_ports"].add(flow["destination_port"])
        w["dst_ips"].add(flow["destination_ip"])
        service = f'{flow["destination_ip"]}:{flow["destination_port"]}'
        w["service_attempts"][service] = w["service_attempts"].get(service, 0) + 1
        w["bytes"] += flow["byte_count"]
    windows = []
    for (source_ip, start_us), w in groups.items():
        windows.append({
            "key_type": "source",
            "source_ip": source_ip,
            "window_start_unix_us": start_us,
            "window_seconds": window_seconds,
            "connection_attempts": w["attempts"],
            "unique_dst_ports": len(w["dst_ports"]),
            "unique_dst_ips": len(w["dst_ips"]),
            "dst_ips": sorted(w["dst_ips"]),
            "service_attempts": w["service_attempts"],   
            "byte_count": w["bytes"],
        })
    return sorted(windows, key=lambda w: (w["window_start_unix_us"], w["source_ip"]))
def build_destination_windows(flows, window_seconds):
    
    groups = {}
    for flow in flows:
        if not is_connection_attempt(flow):
            continue
        key = (flow["destination_ip"], window_start(flow["start_time_unix_us"], window_seconds))
        w = groups.setdefault(key, {"attempts": 0, "src_ips": set(), "dst_ports": set()})
        w["attempts"] += 1
        w["src_ips"].add(flow["source_ip"])
        w["dst_ports"].add(flow["destination_port"])

    windows = []
    for (destination_ip, start_us), w in groups.items():
        windows.append({
            "key_type": "destination",
            "destination_ip": destination_ip,
            "window_start_unix_us": start_us,
            "window_seconds": window_seconds,
            "connection_attempts": w["attempts"],
            "unique_src_ips": len(w["src_ips"]),
            "unique_dst_ports": len(w["dst_ports"]),
        })
    return sorted(windows, key=lambda w: (w["window_start_unix_us"], w["destination_ip"]))