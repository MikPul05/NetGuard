"""Incremental (streaming) wrapper around the batch detection engine.

Flows arrive one by one (e.g. from Kafka). They are kept in a sliding
history buffer; every run() re-evaluates the buffer with the existing
batch engine and returns only detections whose time window has closed
(in event time) and that have not been emitted before.

This module has no Kafka dependency so it can be unit-tested on its own.
"""

import os
import sys
import uuid
from pathlib import Path

ENGINE_DIR = Path(os.environ.get(
    "NETGUARD_ENGINE_DIR",
    Path(__file__).resolve().parent.parent / "detection_engine",
))
sys.path.insert(0, str(ENGINE_DIR))

from combiner import build_output  # noqa: E402
from engine import detect  # noqa: E402
from flow_reader import SUPPORTED_SCHEMA_VERSION  # noqa: E402

US = 1_000_000
# Fixed namespace -> the same detection always gets the same ID (idempotent).
DETECTION_NAMESPACE = uuid.UUID("6f1c3a52-6a1e-4c9e-9d3b-2f6f3f8f0a11")


def parse_flow_event(raw):
    """Return the flow dict from a JSON event, or None if it is invalid."""
    if not isinstance(raw, dict):
        return None
    if raw.get("schema_version") != SUPPORTED_SCHEMA_VERSION:
        return None
    flow = raw.get("flow")
    if not isinstance(flow, dict) or "start_time_unix_us" not in flow:
        return None
    return flow


class StreamingDetector:
    def __init__(self, config, history_seconds=180, grace_seconds=5, input_name="kafka"):
        self.config = config
        self.history_us = history_seconds * US
        self.grace_us = grace_seconds * US
        self.input_name = input_name
        self.flows = []
        self.max_event_us = None
        self.emitted = {}  # key -> window end (for pruning)

    def add(self, flow):
        self.flows.append(flow)
        ts = flow["start_time_unix_us"] + flow.get("duration_us", 0)
        if self.max_event_us is None or ts > self.max_event_us:
            self.max_event_us = ts

    @staticmethod
    def _key(d):
        return (d["type"], d["source_ip"], d["destination_ip"],
                d["window_start_unix_us"], d["window_seconds"])

    def run(self, final=False):
        """Evaluate the buffer. final=True also emits windows that are still open
        (used when the stream goes idle, e.g. at the end of a replay)."""
        if not self.flows:
            return []

        self.flows.sort(key=lambda f: f["start_time_unix_us"])
        result = detect(self.flows, self.config)
        cutoff = self.max_event_us - self.grace_us

        new = []
        for d in result["combined"]:
            window_end = d["window_start_unix_us"] + d["window_seconds"] * US
            if not final and window_end > cutoff:
                continue  # window not closed yet - more flows may still arrive
            key = self._key(d)
            if key in self.emitted:
                continue
            self.emitted[key] = window_end
            new.append(d)

        records = build_output(new, self.input_name)
        for record, d in zip(records, new):
            record["detectionId"] = str(uuid.uuid5(
                DETECTION_NAMESPACE, "|".join(str(p) for p in self._key(d))))

        # Drop flows / emitted keys that fell out of the history buffer.
        keep_from = self.max_event_us - self.history_us
        self.flows = [f for f in self.flows if f["start_time_unix_us"] >= keep_from]
        self.emitted = {k: end for k, end in self.emitted.items() if end >= keep_from}
        return records
