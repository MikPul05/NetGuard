from datetime import datetime, timezone

US = 1_000_000


def windows_overlap(a_start_us, a_seconds, b_start_us, b_seconds):
    return a_start_us < b_start_us + b_seconds * US and b_start_us < a_start_us + a_seconds * US


def same_activity(rule_det, stat_det):
    
    if not windows_overlap(rule_det["window_start_unix_us"], rule_det["window_seconds"],
                           stat_det["window_start_unix_us"], stat_det["window_seconds"]):
        return False
    if rule_det["source_ip"] == stat_det["source_ip"]:
        return True
    return rule_det["source_ip"] == "multiple" and rule_det["destination_ip"] in stat_det["destination_ips"]


def combine(rule_dets, stat_dets):
    combined = [dict(d) for d in rule_dets]
    for s in stat_dets:
        match = next((r for r in combined if same_activity(r, s)), None)
        if match:
            if "statistical" not in match["methods"]:
                match["methods"] = match["methods"] + ["statistical"]
                match["statistical_evidence"] = s["evidence"]
        else:
            combined.append(dict(s))
    return sorted(combined, key=lambda d: d["window_start_unix_us"])


def build_output(dets, input_file):
    
    out = []
    for i, d in enumerate(dets, start=1):
        record = {
            "detectionId": f"d-{i:05d}",
            "timestamp": datetime.fromtimestamp(d["window_start_unix_us"] / US, timezone.utc)
                                 .isoformat().replace("+00:00", "Z"),
            "type": d["type"],
            "sourceIp": d["source_ip"],
            "destinationIp": d["destination_ip"],
            "windowStartUnixUs": d["window_start_unix_us"],
            "windowSeconds": d["window_seconds"],
            "detectionMethods": d["methods"],
            "score": d["score"],
            "evidence": d["evidence"],
            "thresholds": d["thresholds"],
            "input": {"file": input_file},
        }
        if d["statistical_evidence"]:
            record["statisticalEvidence"] = d["statistical_evidence"]
        out.append(record)
    return out