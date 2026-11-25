  export const WINDOW_OPTIONS = [1, 10, 60]          // F05: 1 s, 10 s, 60 s

  export const FEATURE_OPTIONS = {
    connection_attempts: 'Connection attempts',
    unique_dst_ports: 'Unique destination ports',
    unique_dst_ips: 'Unique destination IPs',
    byte_count: 'Bytes',
  }

  const enabled = { key: 'enabled', label: 'Enabled', type: 'bool' }
  const window = { key: 'window_seconds', label: 'Time window', type: 'window' }

  // Which config values the form shows; path = where the section lives in config.toml
  export const CONFIG_SECTIONS = [
    {
      title: 'Port scan rule', path: ['rules', 'port_scan'], fields: [
        enabled, window,
        { key: 'min_unique_dst_ports', label: 'Min. unique destination ports', type: 'int', min: 1,
          help: 'Alert when one source contacts at least this many ports within the window.' },
      ],
    },
    {
      title: 'Brute force rule', path: ['rules', 'brute_force'], fields: [
        enabled, window,
        { key: 'ports', label: 'Watched service ports', type: 'ports', help: 'Comma-separated, e.g. 21, 22, 3389' },
        { key: 'min_attempts', label: 'Min. connection attempts', type: 'int', min: 1 },
      ],
    },
    {
      title: 'DoS / DDoS rule', path: ['rules', 'dos'], fields: [
        enabled, window,
        { key: 'min_attempts_to_destination', label: 'Min. connections to one target', type: 'int', min: 1 },
        { key: 'max_unique_dst_ports', label: 'Max. unique destination ports', type: 'int', min: 1,
          help: 'Targets hit on more ports than this are not reported as DoS.' },
      ],
    },
    {
      title: 'Statistical method (z-score)', path: ['statistical'], fields: [
        enabled, window,
        { key: 'baseline_seconds', label: 'Baseline length (s)', type: 'int', min: 1 },
        { key: 'z_threshold', label: 'Z-score threshold', type: 'float', min: 0 },
        { key: 'min_std', label: 'Minimum standard deviation', type: 'float', min: 0 },
        { key: 'features', label: 'Features', type: 'features' },
      ],
    },
    {
      title: 'Evaluation', path: ['evaluation'], fields: [
        { key: 'window_seconds', label: 'Evaluation window', type: 'window' },
      ],
    },
  ]

  // Copy of DEFAULT_CONFIG in backend/blueprints/config.py - keep the two in sync
  export const DEFAULT_CONFIG = {
    rules: {
      port_scan: { enabled: true, window_seconds: 10, min_unique_dst_ports: 20 },
      brute_force: { enabled: true, window_seconds: 60, ports: [21, 22, 23, 3389], min_attempts: 10 },
      dos: { enabled: true, window_seconds: 10, min_attempts_to_destination: 100, max_unique_dst_ports: 5 },
    },
    statistical: {
      enabled: true, window_seconds: 10, baseline_seconds: 30, z_threshold: 3.0, min_std: 1.0,
      features: ['connection_attempts', 'unique_dst_ports', 'unique_dst_ips', 'byte_count'],
    },
    evaluation: { window_seconds: 10 },
  }