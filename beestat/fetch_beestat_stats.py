#!/usr/bin/env python3
"""Fetch thermostat stats from the beestat API and print a summary.

Usage:
    BEESTAT_API_KEY=yourkey python3 fetch_beestat_stats.py
    # or
    python3 fetch_beestat_stats.py yourkey

Raw JSON responses are saved next to this script as beestat_*.json.
No dependencies beyond the Python standard library.
"""

import json
import os
import sys
import urllib.parse
import urllib.request

BASE = "https://api.beestat.io/"


def call(api_key, resource, method, arguments=None):
    params = {"api_key": api_key, "resource": resource, "method": method}
    if arguments is not None:
        params["arguments"] = json.dumps(arguments)
    url = BASE + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=30) as resp:
        return json.load(resp)


def save(name, payload):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), name)
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"  saved {name}")


def main():
    api_key = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("BEESTAT_API_KEY")
    if not api_key:
        sys.exit("Provide the API key as $BEESTAT_API_KEY or the first argument.")

    thermostats = call(api_key, "thermostat", "read_id")
    save("beestat_thermostats.json", thermostats)
    if not thermostats.get("success", True):
        sys.exit(f"beestat error: {thermostats}")

    sensors = call(api_key, "sensor", "read_id")
    save("beestat_sensors.json", sensors)

    for tid, t in (thermostats.get("data") or {}).items():
        print(f"\nThermostat: {t.get('name', tid)} (id {tid})")
        print(f"  Temperature: {t.get('temperature')}")
        print(f"  Humidity:    {t.get('humidity')}%")
        print(f"  Setpoints:   heat {t.get('setpoint_heat')} / cool {t.get('setpoint_cool')}")
        print(f"  Running:     {t.get('running_equipment')}")
        print(f"  Weather:     {json.dumps(t.get('weather'))[:120]}")
        try:
            summary = call(
                api_key,
                "runtime_thermostat_summary",
                "read_id",
                {"attributes": {"thermostat_id": int(tid)}},
            )
            save(f"beestat_runtime_summary_{tid}.json", summary)
            rows = summary.get("data") or {}
            print(f"  Runtime summary rows: {len(rows)}")
        except Exception as e:  # noqa: BLE001
            print(f"  Runtime summary fetch failed: {e}")

    sensor_data = sensors.get("data") or {}
    if sensor_data:
        print("\nSensors:")
        for s in sensor_data.values():
            print(
                f"  {s.get('name')}: temp {s.get('temperature')}, "
                f"occupancy {s.get('occupancy')}"
            )


if __name__ == "__main__":
    main()
