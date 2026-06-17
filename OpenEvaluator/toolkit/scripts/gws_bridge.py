#!/usr/bin/env python3
"""
Bridge between Hermes OAuth token and gws CLI.

Refreshes the Hermes token (client credentials + refresh_token), then
invokes `gws` with the access token injected as GOOGLE_WORKSPACE_CLI_TOKEN.
"""
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def get_valid_token() -> str:
    """Refresh Hermes token and return a valid access token."""
    token_path = Path.home() / ".hermes" / "google_token.json"
    cred_path = Path.home() / ".hermes" / "google_client_secret.json"

    if not token_path.exists():
        print("ERROR: No Hermes Google token found.", file=sys.stderr)
        sys.exit(1)
    if not cred_path.exists():
        print("ERROR: No Hermes GCP client secret found.", file=sys.stderr)
        sys.exit(1)

    token_data = json.loads(token_path.read_text())
    cred_data = json.loads(cred_path.read_text())

    client_id = cred_data["installed"]["client_id"]
    client_secret = cred_data["installed"]["client_secret"]
    token_uri = cred_data["installed"]["token_uri"]
    refresh_token = token_data["refresh_token"]

    params = urllib.parse.urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }).encode()

    req = urllib.request.Request(token_uri, data=params)
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"ERROR: Token refresh failed (HTTP {e.code}): {body}", file=sys.stderr)
        sys.exit(1)

    return result["access_token"]


def main():
    if len(sys.argv) < 2:
        print("Usage: gws_bridge.py <gws args...>", file=sys.stderr)
        sys.exit(1)

    access_token = get_valid_token()
    env = os.environ.copy()
    env["GOOGLE_WORKSPACE_CLI_TOKEN"] = access_token

    result = subprocess.run(["gws"] + sys.argv[1:], env=env)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()