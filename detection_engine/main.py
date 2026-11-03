import argparse
import json
import os
from collections import Counter

import tomllib

from flow_reader import read_flows
from engine import detect
from combiner import build_output


def main():
    parser = argparse.ArgumentParser(description="NetGuard Detection Engine")
    parser.add_argument("flows", help="flows JSONL file produced by the Flow Extractor")
    parser.add_argument("--config", default="config.toml", help="configuration file with thresholds")
    parser.add_argument("--out", default="detections.jsonl", help="output file for detections")
    args = parser.parse_args()

    with open(args.config, "rb") as f:
        config = tomllib.load(f)

    flows, bad_lines = read_flows(args.flows)
    result = detect(flows, config)
    detections = build_output(result["combined"], os.path.basename(args.flows))

    with open(args.out, "w", encoding="utf-8") as f:
        for d in detections:
            f.write(json.dumps(d) + "\n")

    print(f"Flows read: {len(flows)} (rejected lines: {bad_lines})")
    print(f"Rule-based method:    {len(result['rule'])} detections")
    print(f"Statistical method:   {len(result['statistical'])} detections")
    print(f"Combined:             {len(detections)} detections  {dict(Counter(d['type'] for d in detections))}")
    print()
    for d in detections:
        print(f"[{d['timestamp'][11:19]}] {d['type']:30s} score={d['score']:<6} {'+'.join(d['detectionMethods'])}")
        print(f"           {d['sourceIp']} -> {d['destinationIp']}  {d['evidence']}")
    print(f"\nSaved to {args.out}")


if __name__ == "__main__":
    main()