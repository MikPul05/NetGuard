import urllib.request

endpoints = [
    "/health",
    "/alerts",
    "/alerts/latest",
    "/alerts/1",
    "/detections/d-99999",
    "/detections/d-99999/evidence",
    "/detections/d-99999/trace",
    "/traffic/current",
    "/traffic/timeseries",
    "/traffic/top-talkers",
    "/flows",
    "/stats/summary",
    "/stats/methods",
    "/stats/quality",
    "/config/detection",
    "/sources/",
    "/runs",
]

for ep in endpoints:
    try:
        res = urllib.request.urlopen(f"http://localhost:5000{ep}")
        print(f"[OK]   {ep:32} -> {res.status}")
    except Exception as e:
        print(f"[FAIL] {ep:32} -> {e}")