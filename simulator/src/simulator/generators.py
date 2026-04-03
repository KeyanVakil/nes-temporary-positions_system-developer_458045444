import random
from datetime import UTC, datetime


# Realistic baseline values and noise for drilling parameters
PARAMETER_PROFILES = {
    "rpm": {"base": 120.0, "noise": 10.0, "anomaly_value": 270.0},
    "wob": {"base": 35.0, "noise": 5.0, "anomaly_value": 85.0},
    "torque": {"base": 25.0, "noise": 3.0, "anomaly_value": 90.0},
    "mud_flow_rate": {"base": 2800.0, "noise": 200.0, "anomaly_value": 350.0},
    "vibration": {"base": 3.5, "noise": 1.0, "anomaly_value": 12.5},
}


def generate_reading(anomaly_probability: float = 0.05) -> dict:
    """Generate a single telemetry reading with optional anomaly injection."""
    is_anomaly = random.random() < anomaly_probability
    # Pick one random parameter to spike if anomaly
    anomaly_param = random.choice(list(PARAMETER_PROFILES.keys())) if is_anomaly else None

    reading = {"timestamp": datetime.now(UTC).isoformat()}
    for param, profile in PARAMETER_PROFILES.items():
        if param == anomaly_param:
            value = profile["anomaly_value"] + random.gauss(0, profile["noise"] * 0.5)
        else:
            value = profile["base"] + random.gauss(0, profile["noise"])

        # Clamp to valid ranges
        ranges = {"rpm": (0, 300), "wob": (0, 100), "torque": (0, 100), "mud_flow_rate": (0, 5000), "vibration": (0, 20)}
        lo, hi = ranges[param]
        reading[param] = round(max(lo, min(hi, value)), 2)

    return reading
