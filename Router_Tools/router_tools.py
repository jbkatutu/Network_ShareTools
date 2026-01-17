
#!/usr/bin/env python3
from __future__ import annotations

import sys

from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException

import dev_ipnat_diff
import dev_ipnat_count
import dev_config_diff


def main() -> int:
    try:
        print("\nDev Router Tools")
        print("----------------")
        print("1. dev_ipnat_diff")
        print("2. dev_ipnat_count")
        print("3. dev_config_diff\n")

        choice = input("Select an option (1-3): ").strip()

        if choice == "1":
            dev_ipnat_diff.run()
        elif choice == "2":
            dev_ipnat_count.run()
        elif choice == "3":
            dev_config_diff.run()
        else:
            print("Invalid selection.")
            return 1

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


if __name__ == "__main__":
    raise SystemExit(main())
