#!/usr/bin/env python3
"""Copy the active Grok Build OAuth token into .env as XAI_API_KEY."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUTH_PATH = Path.home() / ".grok" / "auth.json"
ENV_PATH = ROOT / ".env"
EXAMPLE_PATH = ROOT / ".env.example"


def main() -> int:
    if not AUTH_PATH.exists():
        print("No Grok auth found. Log in with Grok Build first, or set XAI_API_KEY manually.")
        print("Manual key: https://console.x.ai/team/default/api-keys")
        return 1

    auth = json.loads(AUTH_PATH.read_text())
    entry = next(iter(auth.values()))
    token = entry.get("key", "").strip()
    if not token:
        print("Grok auth file has no token.")
        return 1

    template = EXAMPLE_PATH.read_text().splitlines() if EXAMPLE_PATH.exists() else ["XAI_API_KEY="]
    lines = []
    replaced = False
    for line in template:
        if line.startswith("XAI_API_KEY="):
            lines.append(f"XAI_API_KEY={token}")
            replaced = True
        else:
            lines.append(line)
    if not replaced:
        lines.insert(0, f"XAI_API_KEY={token}")

    ENV_PATH.write_text("\n".join(lines) + "\n")
    email = entry.get("email", "unknown")
    expires = entry.get("expires_at", "unknown")
    print(f"Updated {ENV_PATH} from Grok Build login ({email})")
    print(f"Token expires: {expires}")
    print("For a non-expiring key, create one at https://console.x.ai/team/default/api-keys")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())