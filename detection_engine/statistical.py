
import statistics

from windows import build_source_windows
from rules import raw_detection

FEATURE_NAMES = {
    "connection_attempts": "connectionAttempts",
    "unique_dst_ports": "uniqueDstPorts",
    "unique_dst_ips": "uniqueDstIps",
    "byte_count": "byteCount",
}
def build_baseline(windows, cfg):
    if not windows:
        return {}
    first = min(w["window_start_unix_us"] for w in windows)
    cutoff = first + cfg["baseline_seconds"] * 1_000_000
    training = [w for w in windows if w["window_start_unix_us"] < cutoff]
    if len(training) < 2:
        training = windows   

    baseline = {}
    for feature in cfg["features"]:
        values = [w[feature] for w in training]
        baseline[feature] = {
            "mean": statistics.mean(values),
            "std": max(statistics.pstdev(values), cfg["min_std"]),
        }
    return baseline


TYPE_BY_FEATURES = [
    ("SUSPICIOUS_CONNECTION_PATTERN", ["unique_dst_ports", "unique_dst_ips"]),  
    ("ABNORMAL_TRAFFIC", ["connection_attempts"]),                             
    ("UNKNOWN_ANOMALY", ["byte_count"]),                                      
]


def classify(z_scores, anomalous_features):
    
    for det_type, features in TYPE_BY_FEATURES:
        hits = [f for f in features if f in anomalous_features]
        if hits:
            return det_type, max(hits, key=lambda f: z_scores[f])
    return "UNKNOWN_ANOMALY", max(anomalous_features, key=lambda f: z_scores[f])

def run_statistical(flows, config):
    cfg = config["statistical"]
    if not cfg["enabled"]:
        return []

    windows = build_source_windows(flows, cfg["window_seconds"])
    baseline = build_baseline(windows, cfg)
    detections = []

    for w in windows:
        z_scores = {
            f: (w[f] - baseline[f]["mean"]) / baseline[f]["std"] for f in cfg["features"]
        }
        anomalous = [f for f, z in z_scores.items() if z > cfg["z_threshold"]]
        if not anomalous:
            continue
        det_type, top = classify(z_scores, anomalous)
        destination = w["dst_ips"][0] if w["unique_dst_ips"] == 1 else "multiple"
        evidence = {FEATURE_NAMES[f]: w[f] for f in cfg["features"]}
        evidence.update({
            "zScore": round(z_scores[top], 2),
            "zScoreFeature": FEATURE_NAMES[top],
            "baselineMean": round(baseline[top]["mean"], 2),
            "baselineStd": round(baseline[top]["std"], 2),
        })
        detections.append(raw_detection(
            det_type, "statistical", w["source_ip"], destination, w["dst_ips"], w,
            evidence=evidence, thresholds={"zScore": cfg["z_threshold"]},
        ))

    return detections