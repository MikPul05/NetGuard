 export const POLL_MS = 3000

  export const TYPE_LABELS = {
    PORT_SCAN: 'Port scan',
    BRUTE_FORCE: 'Brute force',
    DOS_DDOS: 'DoS/DDoS',
    SUSPICIOUS_CONNECTION_PATTERN: 'Suspicious connection pattern',
    ABNORMAL_TRAFFIC: 'Abnormal traffic',
    UNKNOWN_ANOMALY: 'Unknown anomaly',
  }

    export const FEATURE_LABELS = {
    uniqueDstPorts: 'Unique destination ports',
    uniqueDstIps: 'Unique destination IPs',
    uniqueSrcIps: 'Unique source IPs',
    connectionAttempts: 'Connection attempts',
    destinationPort: 'Destination port',
    byteCount: 'Bytes',
    zScore: 'Z-score',
  }
  export const PROTOCOLS = { 1: 'ICMP', 6: 'TCP', 17: 'UDP', 58: 'ICMPv6' }
  export const STAT_META_KEYS = ['zScoreFeature', 'baselineMean', 'baselineStd']