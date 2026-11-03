"""Kafka consumer: flows topic -> detection engine -> detections topic."""

import argparse
import json
import logging
import os
import signal
import time
import tomllib

from confluent_kafka import Consumer, KafkaError, KafkaException, Producer

from streaming_detector import StreamingDetector, parse_flow_event

log = logging.getLogger("netguard.stream_detect")


def main():
    parser = argparse.ArgumentParser(description="NetGuard streaming detector (Kafka)")
    parser.add_argument("--bootstrap", default=os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"))
    parser.add_argument("--in-topic", default=os.environ.get("NETGUARD_FLOWS_TOPIC", "flows"))
    parser.add_argument("--out-topic", default=os.environ.get("NETGUARD_DETECTIONS_TOPIC", "detections"))
    parser.add_argument("--group", default=os.environ.get("NETGUARD_CONSUMER_GROUP", "netguard-detector"))
    parser.add_argument("--config", required=True, help="detection config (config.toml)")
    parser.add_argument("--out", help="also append detections to this JSONL file")
    parser.add_argument("--interval", type=float, default=2.0, help="seconds between detection runs")
    parser.add_argument("--idle-flush", type=float, default=5.0,
                        help="seconds without new flows after which open windows are flushed")
    parser.add_argument("--history", type=int, default=180, help="seconds of event-time history kept")
    parser.add_argument("--grace", type=int, default=5, help="event-time grace period for late flows")
    args = parser.parse_args()

    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"),
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    with open(args.config, "rb") as f:
        config = tomllib.load(f)

    detector = StreamingDetector(config, args.history, args.grace, input_name=f"kafka:{args.in_topic}")
    consumer = Consumer({
        "bootstrap.servers": args.bootstrap,
        "group.id": args.group,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,
    })
    producer = Producer({"bootstrap.servers": args.bootstrap, "enable.idempotence": True})
    consumer.subscribe([args.in_topic])
    log.info("consuming '%s' -> producing '%s' (group=%s, bootstrap=%s)",
             args.in_topic, args.out_topic, args.group, args.bootstrap)

    running = True

    def stop(*_):
        nonlocal running
        running = False

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    out_file = None
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        out_file = open(args.out, "a", encoding="utf-8")

    pending = 0          # flows received since the last detection run
    rejected = 0
    last_run = time.monotonic()
    last_msg = time.monotonic()
    dirty = False        # buffer has flows not yet evaluated with final=True

    try:
        while running:
            for msg in consumer.consume(num_messages=1000, timeout=0.5):
                if msg.error():
                    if msg.error().code() != KafkaError._PARTITION_EOF:
                        log.warning("consumer error: %s", msg.error())
                    continue
                try:
                    flow = parse_flow_event(json.loads(msg.value()))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    flow = None
                if flow is None:
                    rejected += 1
                    continue
                detector.add(flow)
                pending += 1
                dirty = True
                last_msg = time.monotonic()

            now = time.monotonic()
            idle = dirty and now - last_msg >= args.idle_flush
            if not (pending and now - last_run >= args.interval) and not idle:
                continue

            started = time.monotonic()
            records = detector.run(final=idle)
            for record in records:
                value = json.dumps(record)
                producer.produce(args.out_topic, key=record["sourceIp"], value=value)
                if out_file:
                    out_file.write(value + "\n")
                log.info("DETECTION %s %s -> %s score=%s methods=%s id=%s",
                         record["type"], record["sourceIp"], record["destinationIp"],
                         record["score"], "+".join(record["detectionMethods"]), record["detectionId"])
            producer.flush(10)
            if out_file:
                out_file.flush()
            if pending:
                try:
                    consumer.commit(asynchronous=False)
                except KafkaException as e:
                    if e.args[0].code() != KafkaError._NO_OFFSET:
                        raise
            log.info("run: %d new flows, %d buffered, %d rejected, %d detections, %.0f ms%s",
                     pending, len(detector.flows), rejected, len(records),
                     (time.monotonic() - started) * 1000, " (idle flush)" if idle else "")
            pending = 0
            last_run = now
            if idle:
                dirty = False
    finally:
        log.info("shutting down")
        consumer.close()
        producer.flush(10)
        if out_file:
            out_file.close()


if __name__ == "__main__":
    main()
