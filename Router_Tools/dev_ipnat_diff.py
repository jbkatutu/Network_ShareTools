#!/usr/bin/env python3
from __future__ import annotations

import os
import time
from pathlib import Path

from dotenv import load_dotenv
from netmiko import ConnectHandler

# Load .env from same directory as this file
load_dotenv(dotenv_path=Path(__file__).with_name(".env"))

NAT_MATCH = "ip nat inside source static"


def _get_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _build_device(host: str) -> dict:
    return {
        "device_type": _get_env("DEV_CISCO_DEVICE_TYPE"),
        "host": host,
        "username": _get_env("DEV_CISCO_USERNAME"),
        "password": _get_env("DEV_CISCO_PASSWORD"),
        "port": int(_get_env("DEV_CISCO_PORT")),
        "timeout": 30,
    }


def _connect_and_run(device: dict, command: str, timeout: int = 120) -> str:
    with ConnectHandler(**device) as conn:
        conn.disable_paging()
        return conn.send_command(command, read_timeout=timeout)


def _get_static_nat_count(device: dict) -> int:
    cmd = f"show running-config | include {NAT_MATCH}"
    output = _connect_and_run(device, cmd)
    return sum(1 for line in output.splitlines() if line.strip().startswith(NAT_MATCH))


def run() -> None:
    dev1 = _build_device(_get_env("DEV_CISCO_HOST_1"))
    dev2 = _build_device(_get_env("DEV_CISCO_HOST_2"))

    start = time.time()
    count1 = _get_static_nat_count(dev1)
    count2 = _get_static_nat_count(dev2)
    elapsed = time.time() - start
    delta = count1 - count2

    print("\nMode:   dev_ipnat_diff")
    print(f"Match:  {NAT_MATCH}")
    print(f"Router 1: {dev1['host']}  Count: {count1}")
    print(f"Router 2: {dev2['host']}  Count: {count2}")
    print(f"Delta:  {delta}  (Router1 - Router2)")
    print(f"Took:   {elapsed:.2f}s\n")
