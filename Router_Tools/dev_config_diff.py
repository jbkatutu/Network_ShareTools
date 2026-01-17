#!/usr/bin/env python3
from __future__ import annotations

import os
import time
import difflib
from pathlib import Path

from dotenv import load_dotenv
from netmiko import ConnectHandler

# Load .env from same directory as this file
load_dotenv(dotenv_path=Path(__file__).with_name(".env"))


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


def _clean_running_config(output: str) -> list[str]:
    cleaned: list[str] = []
    for line in output.splitlines():
        line = line.rstrip()
        if not line:
            continue
        if line.startswith("!"):
            continue
        if line in ("end",):
            continue
        if "Last configuration change" in line:
            continue
        cleaned.append(line)
    return cleaned


def _get_running_config(device: dict) -> list[str]:
    out = _connect_and_run(device, "show running-config", timeout=300)
    return _clean_running_config(out)


def run() -> None:
    dev1 = _build_device(_get_env("DEV_CISCO_HOST_1"))
    dev2 = _build_device(_get_env("DEV_CISCO_HOST_2"))

    start = time.time()
    cfg1 = _get_running_config(dev1)
    cfg2 = _get_running_config(dev2)

    diff_lines = list(
        difflib.unified_diff(
            cfg1,
            cfg2,
            fromfile=f"{dev1['host']}:running-config",
            tofile=f"{dev2['host']}:running-config",
            lineterm="",
        )
    )
    elapsed = time.time() - start

    print("\nMode:   dev_config_diff")
    print(f"Router 1: {dev1['host']}")
    print(f"Router 2: {dev2['host']}")
    print(f"Took:   {elapsed:.2f}s\n")

    if diff_lines:
        for line in diff_lines:
            print(line)
    else:
        print("Result: configs match (after cleanup).")
