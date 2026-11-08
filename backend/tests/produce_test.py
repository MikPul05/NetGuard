import json
from kafka import KafkaProducer

producer = KafkaProducer(
    bootstrap_servers='kafka:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

event = {
    "detectionId": "d-99999",
    "timestamp": "2026-11-08T18:00:00Z",
    "type": "PORT_SCAN",
    "sourceIp": "10.10.10.50",
    "destinationIp": "192.168.1.1",
    "windowStartUnixUs": 1731088800000000,
    "windowSeconds": 10,
    "detectionMethods": ["rule"],
    "score": 2.5,
    "evidence": {"uniqueDstPorts": 30, "connectionAttempts": 30},
    "thresholds": {"uniqueDstPorts": 20},
    "input": {"file": "live_stream"}
}

producer.send('detections', event)
producer.flush()
print("Test detection d-99999 published successfully!")