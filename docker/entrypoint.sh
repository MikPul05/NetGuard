#!/bin/sh
# NetGuard container entrypoint.
# Paths are resolved relative to /data (the mounted volume) unless absolute.
set -eu

ENGINE_DIR=/app/detection_engine
DEFAULT_CONFIG="$ENGINE_DIR/config.toml"

usage() {
    cat <<EOF
NetGuard (Docker)

Usage:
  netguard extract  <input.pcap|pcapng> <flows.jsonl>
      Run the C++ importer: PCAP/PCAPNG -> normalized flows (JSONL).

  netguard detect   <flows.jsonl> [--config FILE] [--out FILE]
      Run the Python detection engine on a flows file.

  netguard evaluate <flows.jsonl> <labels.csv> [--config FILE]
      Evaluate detections against ground-truth labels.

  netguard pipeline <input.pcap|pcapng> [output_dir]
      extract + detect in one go. Writes <output_dir>/flows.jsonl and
      <output_dir>/detections.jsonl (default output_dir: out, i.e. /data/out).

  netguard demo
      Run the detection engine on the bundled sample flows.

  netguard shell | sh | bash
      Open a shell inside the container.

Without --config the bundled $DEFAULT_CONFIG is used. To override it,
place your own config.toml in the mounted /data directory and pass
--config config.toml.
EOF
}

# Append the default config unless the user passed --config.
with_default_config() {
    for arg in "$@"; do
        case "$arg" in
            --config|--config=*) return 1 ;;
        esac
    done
    return 0
}

extract() {
    if [ "$#" -ne 2 ]; then
        echo "extract: expected <input.pcap> <flows.jsonl>" >&2
        exit 2
    fi
    if [ ! -f "$1" ]; then
        echo "extract: input file not found: $1 (is it inside the mounted /data volume?)" >&2
        exit 1
    fi
    mkdir -p "$(dirname "$2")"
    # The importer reads both paths interactively from stdin.
    printf '%s\n%s\n' "$1" "$2" | netguard-importer
    echo
}

detect() {
    if with_default_config "$@"; then
        set -- "$@" --config "$DEFAULT_CONFIG"
    fi
    python "$ENGINE_DIR/main.py" "$@"
}

evaluate() {
    if with_default_config "$@"; then
        set -- "$@" --config "$DEFAULT_CONFIG"
    fi
    python "$ENGINE_DIR/evaluate.py" "$@"
}

cmd="${1:-help}"
[ "$#" -gt 0 ] && shift

case "$cmd" in
    extract)  extract "$@" ;;
    detect)   detect "$@" ;;
    evaluate) evaluate "$@" ;;
    pipeline)
        if [ "$#" -lt 1 ]; then
            echo "pipeline: expected <input.pcap> [output_dir]" >&2
            exit 2
        fi
        out_dir="${2:-out}"
        extract "$1" "$out_dir/flows.jsonl"
        detect "$out_dir/flows.jsonl" --out "$out_dir/detections.jsonl"
        ;;
    demo)
        detect "$ENGINE_DIR/sample_data/flows_example.jsonl" --out /data/demo_detections.jsonl
        ;;
    shell|sh|bash) exec /bin/sh "$@" ;;
    help|-h|--help) usage ;;
    *)
        echo "Unknown command: $cmd" >&2
        usage >&2
        exit 2
        ;;
esac
