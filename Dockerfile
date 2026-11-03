# syntax=docker/dockerfile:1

# ---------------------------------------------------------------------------
# Stage 1: build the C++ PCAP importer / flow extractor
# ---------------------------------------------------------------------------
FROM debian:bookworm-slim AS builder

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
        libpcap-dev \
        rapidjson-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src
COPY CMakeLists.txt ./
COPY importer ./importer

RUN cmake -S . -B build -DCMAKE_BUILD_TYPE=Release \
    && cmake --build build -j"$(nproc)" \
    && cmake --install build --prefix /opt/netguard

# ---------------------------------------------------------------------------
# Stage 2: runtime image (importer binary + Python detection engine)
# ---------------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpcap0.8 \
    && rm -rf /var/lib/apt/lists/*

COPY streaming/requirements.txt /tmp/streaming-requirements.txt
RUN pip install --no-cache-dir -r /tmp/streaming-requirements.txt \
    && rm /tmp/streaming-requirements.txt

COPY --from=builder /opt/netguard/bin/NetGuard /usr/local/bin/netguard-importer
COPY detection_engine /app/detection_engine
COPY streaming /app/streaming
COPY docker/entrypoint.sh /usr/local/bin/netguard
RUN chmod +x /usr/local/bin/netguard \
    && useradd --create-home --uid 1000 netguard \
    && mkdir -p /data \
    && chown netguard:netguard /data

USER netguard
WORKDIR /data
VOLUME ["/data"]

ENTRYPOINT ["netguard"]
CMD ["help"]
