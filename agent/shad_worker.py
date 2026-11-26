"""Fail-closed Shad worker scaffold.

This process intentionally does not authenticate, fetch updates, read history,
or send messages. The aioshad documentation does not specify whether a fresh
client's initial update state excludes pre-activation messages, so live polling
must remain blocked until that behavior is verified in an isolated test.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name, str(default)).strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off", ""}:
        return False
    raise ValueError(f"{name} must be a boolean value")


def main() -> int:
    enabled = env_bool("SHAD_ENABLED", False)
    dry_run = env_bool("SHAD_DRY_RUN", True)
    auto_reply = env_bool("SHAD_AUTO_REPLY", False)
    group_guid = os.getenv("SHAD_GROUP_GUID", "").strip()
    session_dir = Path(os.getenv("SHAD_SESSION_DIR", "/run/secrets/shad")).resolve()

    report = {
        "component": "shad-worker",
        "enabled": enabled,
        "dry_run": dry_run,
        "auto_reply": auto_reply,
        "group_configured": bool(group_guid),
        "session_directory_configured": bool(str(session_dir)),
        "mode": "preflight_only",
    }

    # Never print phone numbers, group messages, session contents, or secrets.
    print(json.dumps(report, ensure_ascii=False))

    if not enabled:
        print("Shad worker is disabled; no account access or network activity.")
        return 0

    if not group_guid:
        print("Refusing to start: SHAD_GROUP_GUID is missing.", file=sys.stderr)
        return 2

    if not dry_run or auto_reply:
        print(
            "Refusing live operation: update-baseline safety has not been "
            "verified and message handlers are not enabled.",
            file=sys.stderr,
        )
        return 3

    # Even dry-run network polling is deliberately disabled for now: the
    # documented update API does not define a safe activation cursor contract.
    print(
        "Preflight passed, but network polling is blocked until a controlled "
        "test proves that only post-activation updates are delivered."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
