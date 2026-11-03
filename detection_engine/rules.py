from windows import build_source_windows, build_destination_windows


def raw_detection(det_type, method, source_ip, destination_ip, destination_ips,
                  window, evidence, thresholds):
    score = max(evidence[name] / limit for name, limit in thresholds.items())
    return {
        "type": det_type,
        "methods": [method],
        "source_ip": source_ip,
        "destination_ip": destination_ip,
        "destination_ips": destination_ips,      
        "window_start_unix_us": window["window_start_unix_us"],
        "window_seconds": window["window_seconds"],
        "evidence": evidence,                    
        "thresholds": thresholds,                
        "score": round(score, 2),
        "statistical_evidence": None,            
    }

def port_scan(window, cfg):
    ports = window["unique_dst_ports"]
    if ports < cfg["min_unique_dst_ports"]:
        return None
    destination = window["dst_ips"][0] if window["unique_dst_ips"] == 1 else "multiple"
    return raw_detection(
        "PORT_SCAN", "rule", window["source_ip"], destination, window["dst_ips"], window,
        evidence={"uniqueDstPorts": ports, "connectionAttempts": window["connection_attempts"]},
        thresholds={"uniqueDstPorts": cfg["min_unique_dst_ports"]},
    )
def brute_force(window, cfg):
    detections = []
    for service, attempts in window["service_attempts"].items():
        ip, port = service.rsplit(":", 1)
        if int(port) in cfg["ports"] and attempts >= cfg["min_attempts"]:
            detections.append(raw_detection(
                "BRUTE_FORCE", "rule", window["source_ip"], ip, [ip], window,
                evidence={"connectionAttempts": attempts, "destinationPort": int(port)},
                thresholds={"connectionAttempts": cfg["min_attempts"]},
            ))
    return detections

def dos(window, cfg):
    attempts = window["connection_attempts"]
    if attempts < cfg["min_attempts_to_destination"]:
        return None
    if window["unique_dst_ports"] > cfg["max_unique_dst_ports"]:
        return None
    return raw_detection(
        "DOS_DDOS", "rule", "multiple", window["destination_ip"], [window["destination_ip"]], window,
        evidence={"connectionAttempts": attempts, "uniqueSrcIps": window["unique_src_ips"],
                  "uniqueDstPorts": window["unique_dst_ports"]},
        thresholds={"connectionAttempts": cfg["min_attempts_to_destination"]},
    )

def run_rules(flows, config):
    rules_cfg = config["rules"]
    detections = []

    if rules_cfg["port_scan"]["enabled"]:
        cfg = rules_cfg["port_scan"]
        for w in build_source_windows(flows, cfg["window_seconds"]):
            d = port_scan(w, cfg)
            if d:
                detections.append(d)

    if rules_cfg["brute_force"]["enabled"]:
        cfg = rules_cfg["brute_force"]
        for w in build_source_windows(flows, cfg["window_seconds"]):
            detections.extend(brute_force(w, cfg))

    if rules_cfg["dos"]["enabled"]:
        cfg = rules_cfg["dos"]
        for w in build_destination_windows(flows, cfg["window_seconds"]):
            d = dos(w, cfg)
            if d:
                detections.append(d)

    return sorted(detections, key=lambda d: d["window_start_unix_us"])



