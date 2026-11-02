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
    parser.add_argument("flows", help="plik JSONL z Flow Extractora")
    parser.add_argument("--config", default="config.toml", help="plik z progami")
    parser.add_argument("--out", default="detections.jsonl", help="gdzie zapisać detekcje")
    args = parser.parse_args()

    with open(args.config, "rb") as f:      
        config = tomllib.load(f)

    flows, bad_lines = read_flows(args.flows)
    result = detect(flows, config)
    detections = build_output(result["combined"], os.path.basename(args.flows))

    with open(args.out, "w", encoding="utf-8") as f:
        for d in detections:
            f.write(json.dumps(d) + "\n")

    print(f"Flows wczytane: {len(flows)} (odrzucone linie: {bad_lines})")
    print(f"Metoda regułowa:      {len(result['rule'])} detekcji")
    print(f"Metoda statystyczna:  {len(result['statistical'])} detekcji")
    print(f"Po połączeniu:        {len(detections)} detekcji  {dict(Counter(d['type'] for d in detections))}")
    print()
    for d in detections:
        print(f"[{d['timestamp'][11:19]}] {d['type']:30s} score={d['score']:<6} {'+'.join(d['detectionMethods'])}")
        print(f"           {d['sourceIp']} -> {d['destinationIp']}  {d['evidence']}")
    print(f"\nZapisano do {args.out}")


if __name__ == "__main__":
    main()