"""Kafka producer: publish a flows JSONL file (importer output) to the flows topic."""

import argparse
import json
import os
import time

from confluent_kafka import Producer

from streaming_detector import parse_flow_event


def main():
    parser = argparse.ArgumentParser(description="Publish NetGuard flows to Kafka")
    parser.add_argument("flows", help="flows JSONL file produced by the importer")
    parser.add_argument("--bootstrap", default=os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"))
    parser.add_argument("--topic", default=os.environ.get("NETGUARD_FLOWS_TOPIC", "flows"))
    parser.add_argument("--rate", type=float, default=0,
                        help="max flows per second (0 = as fast as possible)")
    args = parser.parse_args()

    events = []
    rejected = 0
    with open(args.flows, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                rejected += 1
                continue
            if parse_flow_event(event) is None:
                rejected += 1
                continue
            events.append(event)

    # Send in event-time order so the detector's time windows close correctly.
    events.sort(key=lambda e: e["flow"]["start_time_unix_us"])

    failed = 0

    def on_delivery(err, _msg):
        nonlocal failed
        if err is not None:
            failed += 1

    producer = Producer({
        "bootstrap.servers": args.bootstrap,
        "enable.idempotence": True,
        "linger.ms": 20,
    })

    started = time.monotonic()
    for i, event in enumerate(events):
        if args.rate > 0:
            delay = started + i / args.rate - time.monotonic()
            if delay > 0:
                time.sleep(delay)
        while True:
            try:
                producer.produce(args.topic, key=event["flow"]["source_ip"],
                                 value=json.dumps(event), on_delivery=on_delivery)
                break
            except BufferError:
                producer.poll(0.5)  # local queue full - let it drain
        producer.poll(0)

    remaining = producer.flush(30)
    elapsed = time.monotonic() - started
    sent = len(events) - failed - remaining
    print(f"Published {sent} flows to '{args.topic}' in {elapsed:.2f}s "
          f"({sent / elapsed if elapsed else 0:.0f} flows/s); "
          f"rejected lines: {rejected}, failed: {failed + remaining}")
    if failed or remaining:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
