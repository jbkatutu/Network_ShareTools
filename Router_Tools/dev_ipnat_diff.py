#!/usr/bin/env python3
"""
Cisco Static NAT HA parity checker (IOS / IOS-XE)

- Connects to two routers via SSH
- Pulls static NAT config lines:
    ip nat inside source static <inside-ip> <public-ip> ...
- Prints per-router summary (Router/Match/Count/Took)
- Compares NAT entries by PUBLIC IP (semantic comparison)
- Outputs:
  1) SAFE MISSING on Router1 (copy/paste allowed)
  2) SAFE MISSING on Router2 (copy/paste allowed)
  3) CONFLICTS (same public IP, different inside IPs — DO NOT paste blindly)

Requirements:
  pip install netmiko python-dotenv
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

from dotenv import load_dotenv
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException

# Load .env from the same directory as this script
load_dotenv(dotenv_path=Path(__file__).with_name(".env"))

NAT_MATCH = "ip nat inside source static"


def get_env(name: str) -> str:
    val = os.getenv(name, "").strip()
    if not val:
        raise RuntimeError(f"Missing env var: {name}")
    return val


def parse_nat(line: str) -> Tuple[str, str]:
    """
    Parses:
      ip nat inside source static <inside_ip> <public_ip> [options...]
    Returns:
      (inside_ip, public_ip)
    """
    parts = line.split()
    if len(parts) < 7:
        raise ValueError(f"Invalid NAT line: {line}")
    return parts[5], parts[6]


def fetch_nat_lines(host: str, username: str, password: str, device_type: str, port: int, timeout: int = 30) -> List[str]:
    device = {
        "device_type": device_type,
        "host": host,
        "username": username,
        "password": password,
        "port": port,
        "timeout": timeout,
    }

    cmd = f"show running-config | include {NAT_MATCH}"

    with ConnectHandler(**device) as conn:
        conn.disable_paging()
        output = conn.send_command(cmd, read_timeout=timeout)

    # De-dup and keep stable order
    return sorted({l.strip() for l in output.splitlines() if l.strip().startswith(NAT_MATCH)})


def build_public_map(lines: List[str]) -> Dict[str, str]:
    """
    Map: public_ip -> full CLI line (first seen)
    """
    m: Dict[str, str] = {}
    for line in lines:
        inside, public = parse_nat(line)
        if public not in m:
            m[public] = line
    return m


def print_router_summary(host: str, count: int, elapsed: float) -> None:
    print(f"Router: {host}")
    print(f"Match:  {NAT_MATCH}")
    print(f"Count:  {count}")
    print(f"Took:   {elapsed:.2f}s\n")


def print_missing_section(title: str, lines: List[str]) -> None:
    print(title)
    print(f"Count:  {len(lines)}")
    if lines:
        print("----")
        for line in lines:
            print(line)
        print("----")
    print("")


def main() -> int:
    try:
        r1 = get_env("DEV_CISCO_HOST_1")
        r2 = get_env("DEV_CISCO_HOST_2")
        username = get_env("DEV_CISCO_USERNAME")
        password = get_env("DEV_CISCO_PASSWORD")
        device_type = os.getenv("DEV_CISCO_DEVICE_TYPE", "cisco_ios").strip() or "cisco_ios"
        port = int(os.getenv("DEV_CISCO_PORT", "22").strip())

        # Router1 fetch + timing
        t0 = time.time()
        r1_lines = fetch_nat_lines(r1, username, password, device_type, port)
        r1_time = time.time() - t0

        # Router2 fetch + timing
        t0 = time.time()
        r2_lines = fetch_nat_lines(r2, username, password, device_type, port)
        r2_time = time.time() - t0

        # REQUIRED summaries (kept)
        print_router_summary(r1, len(r1_lines), r1_time)
        print_router_summary(r2, len(r2_lines), r2_time)

        # Build maps: public_ip -> cli_line
        r1_map = build_public_map(r1_lines)
        r2_map = build_public_map(r2_lines)

        r1_public = set(r1_map.keys())
        r2_public = set(r2_map.keys())

        # SAFE missing by PUBLIC IP (true absence)
        missing_on_r1_public = sorted(r2_public - r1_public)  # exists on R2, not on R1
        missing_on_r2_public = sorted(r1_public - r2_public)  # exists on R1, not on R2

        missing_on_r1_lines = [r2_map[p] for p in missing_on_r1_public]
        missing_on_r2_lines = [r1_map[p] for p in missing_on_r2_public]

        print_missing_section(
            f"Below are SAFE MISSING entries on Router1 {r1}, but EXIST on Router2 {r2} (copy/paste allowed)",
            missing_on_r1_lines,
        )

        print_missing_section(
            f"Below are SAFE MISSING entries on Router2 {r2}, but EXIST on Router1 {r1} (copy/paste allowed)",
            missing_on_r2_lines,
        )

        # Conflicts: same public IP exists on both but different inside IP
        conflicts_public = sorted(
            p for p in (r1_public & r2_public)
            if parse_nat(r1_map[p])[0] != parse_nat(r2_map[p])[0]
        )

        print("CONFLICTS (same public IP, different inside IPs — DO NOT paste blindly)")
        print(f"Count: {len(conflicts_public)}")
        if conflicts_public:
            print("----")
            for public in conflicts_public:
                print(f"# Router1 {r1}")
                print(r1_map[public])
                print(f"# Router2 {r2}")
                print(r2_map[public])
                print("")
            print("----")
        print("")

        return 0

    except NetmikoTimeoutException:
        print("ERROR: SSH timeout", file=sys.stderr)
        return 2
    except NetmikoAuthenticationException:
        print("ERROR: Authentication failed", file=sys.stderr)
        return 3
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 4

def run() -> None:
    raise SystemExit(main())

if __name__ == "__main__":
    raise SystemExit(main())
