import asyncio
import logging
import sys

import httpx

from simulator.config import config
from simulator.generators import generate_reading

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("simulator")

RIG_NAMES = [
    ("Rig Alpha-1", "drilling_rig", "North Sea Platform A"),
    ("Rig Bravo-2", "drilling_rig", "North Sea Platform B"),
    ("Rig Charlie-3", "drilling_rig", "Barents Sea Platform C"),
    ("Mud Pump Delta", "mud_pump", "North Sea Platform A"),
    ("Rig Echo-5", "drilling_rig", "Norwegian Sea Platform D"),
]


async def wait_for_api(client: httpx.AsyncClient) -> None:
    """Wait until the API is healthy."""
    url = f"{config.api_base_url}/api/v1/health"
    for attempt in range(60):
        try:
            resp = await client.get(url, timeout=5)
            if resp.status_code == 200:
                log.info("API is ready")
                return
        except httpx.RequestError:
            pass
        log.info("Waiting for API... (attempt %d)", attempt + 1)
        await asyncio.sleep(2)
    log.error("API not available after 120s, exiting")
    sys.exit(1)


async def register_devices(client: httpx.AsyncClient) -> list[dict]:
    """Register simulator devices, returning their IDs."""
    devices = []
    for i in range(config.device_count):
        name, dtype, location = RIG_NAMES[i % len(RIG_NAMES)]
        payload = {"name": name, "device_type": dtype, "location": location}
        resp = await client.post(f"{config.api_base_url}/api/v1/devices", json=payload)
        if resp.status_code == 201:
            device = resp.json()["data"]
            log.info("Registered device: %s (id=%s)", name, device["id"])
            devices.append(device)
        elif resp.status_code == 409:
            # Already exists, fetch it
            list_resp = await client.get(f"{config.api_base_url}/api/v1/devices")
            for d in list_resp.json()["data"]:
                if d["name"] == name:
                    devices.append(d)
                    log.info("Device already exists: %s (id=%s)", name, d["id"])
                    break
        else:
            log.error("Failed to register %s: %d %s", name, resp.status_code, resp.text)
    return devices


async def telemetry_loop(client: httpx.AsyncClient, devices: list[dict]) -> None:
    """Continuously send telemetry for all devices."""
    while True:
        for device in devices:
            reading = generate_reading(config.anomaly_probability)
            payload = {"device_id": device["id"], "readings": [reading]}
            try:
                resp = await client.post(
                    f"{config.api_base_url}/api/v1/telemetry", json=payload, timeout=10
                )
                log.info(
                    "POST telemetry device=%s status=%d rpm=%.1f vib=%.1f",
                    device["id"][:8],
                    resp.status_code,
                    reading["rpm"],
                    reading["vibration"],
                )
            except httpx.RequestError as e:
                log.warning("Failed to send telemetry for %s: %s", device["id"][:8], e)
        await asyncio.sleep(config.interval_seconds)


async def main() -> None:
    async with httpx.AsyncClient() as client:
        await wait_for_api(client)
        devices = await register_devices(client)
        if not devices:
            log.error("No devices registered, exiting")
            sys.exit(1)
        log.info("Starting telemetry loop for %d devices", len(devices))
        await telemetry_loop(client, devices)


if __name__ == "__main__":
    asyncio.run(main())
