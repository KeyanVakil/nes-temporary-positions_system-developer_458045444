import os


class SimConfig:
    device_count: int = int(os.environ.get("SIM_DEVICE_COUNT", "3"))
    interval_seconds: float = float(os.environ.get("SIM_INTERVAL_SECONDS", "2"))
    anomaly_probability: float = float(os.environ.get("SIM_ANOMALY_PROBABILITY", "0.05"))
    api_base_url: str = os.environ.get("SIM_API_BASE_URL", "http://api:8000")


config = SimConfig()
