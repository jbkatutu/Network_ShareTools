# Dev Router Tools (Cisco IOS / IOS-XE)

A modular, menu-driven toolkit for Cisco IOS / IOS-XE routers designed to help **network engineers and automation developers** audit, compare, and validate router configuration and NAT state in a safe, deterministic way.

This toolset intentionally separates **configuration truth** from **runtime behavior**, reducing false alarms caused by NAT translation fluctuations.

---

## Features

When you run:

```bash
python3 dev_router_tools.py
```

You are presented with:

```
1. dev_ipnat_diff
2. dev_ipnat_count
3. dev_config_diff
```

Each option runs a dedicated tool from its own file.

---

## Tool Overview

### 1️⃣ dev_ipnat_diff
Compare static NAT counts between two routers.

- Counts `ip nat inside source static` on both routers
- Displays delta (Router1 - Router2)
- Ideal for HA parity checks and migration validation

---

### 2️⃣ dev_ipnat_count
Count static NATs on a single router.

- Stable baseline independent of traffic
- Suitable for audits and capacity planning

---

### 3️⃣ dev_config_diff
Compare running-config between two routers.

- Removes noisy lines (timestamps, comments)
- Produces a clean unified diff
- Useful for HA validation and troubleshooting

---

## Directory Structure

```
IP_NAT/
├── .env
├── dev_router_tools.py
├── dev_ipnat_diff.py
├── dev_ipnat_count.py
└── dev_config_diff.py
```

---

## Requirements

- Python 3.9+
- SSH access to Cisco IOS / IOS-XE routers

Python dependencies:
```bash
pip install netmiko python-dotenv
```

---

## Configuration (.env)

```env
DEV_CISCO_HOST_1=10.50.0.4
DEV_CISCO_HOST_2=10.50.0.47
DEV_CISCO_USERNAME=admin
DEV_CISCO_PASSWORD=YourPassword
DEV_CISCO_DEVICE_TYPE=cisco_ios
DEV_CISCO_PORT=22
```

---

## Running the Tools

```bash
cd IP_NAT
python3 dev_router_tools.py
```

---

## NAT Design Philosophy

This toolkit intentionally counts static NATs via configuration:

```bash
show running-config | include ip nat inside source static
```

Instead of relying on:

```bash
show ip nat translations
```

Because translation tables reflect runtime traffic and fluctuate by design.

---

## Security Notes

- Never commit `.env`
- Add `.env` to `.gitignore`
- Use automation-specific credentials

---

## License

Internal / project use.
