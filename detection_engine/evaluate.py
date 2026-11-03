import argparse
import csv
import ipaddress

import tomllib

from flow_reader import read_flows, is_connection_attempt
from windows import window_start
from engine import detect

US = 1_000_000


def read_labels(path):
    labels = []
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            labels.append({
                "start_us": int(float(row["start_unix_s"]) * US),
                "end_us": int(float(row["end_unix_s"]) * US),
                "source": ipaddress.ip_network(row["source_ip"]),
                "destination_ip": row["destination_ip"],
                "attack_type": row["attack_type"],
            })
    return labels


def build_units(flows, window_seconds):
    units = {}
    for flow in flows:
        if is_connection_attempt(flow):
            key = (flow["source_ip"], window_start(flow["start_time_unix_us"], window_seconds))
            units.setdefault(key, set()).add(flow["destination_ip"])
    return units


def unit_is_attack(src, start_us, window_seconds, labels):
    end_us = start_us + window_seconds * US
    for lab in labels:
        if lab["start_us"] < end_us and lab["end_us"] >= start_us and ipaddress.ip_address(src) in lab["source"]:
            return lab
    return None


def unit_is_flagged(src, start_us, window_seconds, dsts, detections):
    end_us = start_us + window_seconds * US
    for d in detections:
        d_end = d["window_start_unix_us"] + d["window_seconds"] * US
        if not (d["window_start_unix_us"] < end_us and d_end > start_us):
            continue
        if d["source_ip"] == src:
            return True
        if d["source_ip"] == "multiple" and d["destination_ip"] in dsts:
            return True
    return False


def metrics(units, labels, detections, window_seconds):
    tp = fp = fn = tn = 0
    detected_labels = set()
    for (src, start_us), dsts in units.items():
        label = unit_is_attack(src, start_us, window_seconds, labels)
        flagged = unit_is_flagged(src, start_us, window_seconds, dsts, detections)
        if label and flagged:
            tp += 1
            detected_labels.add(label["attack_type"])
        elif flagged:
            fp += 1
        elif label:
            fn += 1
        else:
            tn += 1

    def div(a, b):
        return a / b if b else 0.0

    precision = div(tp, tp + fp)
    recall = div(tp, tp + fn)
    return {
        "TP": tp, "FP": fp, "FN": fn, "TN": tn,
        "precision": precision,
        "recall": recall,
        "F1": div(2 * precision * recall, precision + recall),
        "FPR": div(fp, fp + tn),
        "FNR": div(fn, fn + tp),
        "detected_attacks": detected_labels,
    }


def main():
    parser = argparse.ArgumentParser(description="NetGuard - detection quality evaluation")
    parser.add_argument("flows", help="flows JSONL file produced by the Flow Extractor")
    parser.add_argument("labels", help="ground truth labels CSV file")
    parser.add_argument("--config", default="config.toml", help="configuration file with thresholds")
    args = parser.parse_args()

    with open(args.config, "rb") as f:
        config = tomllib.load(f)

    flows, _ = read_flows(args.flows)
    labels = read_labels(args.labels)
    result = detect(flows, config)
    w = config["evaluation"]["window_seconds"]
    units = build_units(flows, w)

    print(f"Evaluation units: {len(units)}  (host, {w} s window)")
    print(f"Labelled attacks: {', '.join(l['attack_type'] for l in labels)}\n")
    print(f"{'Method':14s} {'TP':>4s} {'FP':>4s} {'FN':>4s} {'TN':>5s} "
          f"{'Precision':>10s} {'Recall':>7s} {'F1':>6s} {'FPR':>6s} {'FNR':>6s}")
    for name in ["rule", "statistical", "combined"]:
        m = metrics(units, labels, result[name], w)
        print(f"{name:14s} {m['TP']:4d} {m['FP']:4d} {m['FN']:4d} {m['TN']:5d} "
              f"{m['precision']:10.3f} {m['recall']:7.3f} {m['F1']:6.3f} {m['FPR']:6.3f} {m['FNR']:6.3f}")

    print("\nAttacks detected by each method:")
    all_types = [l["attack_type"] for l in labels]
    for name in ["rule", "statistical", "combined"]:
        found = metrics(units, labels, result[name], w)["detected_attacks"]
        marks = "  ".join(f"{t}:{'YES' if t in found else 'no'}" for t in all_types)
        print(f"  {name:12s} {marks}")


if __name__ == "__main__":
    main()