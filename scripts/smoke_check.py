#!/usr/bin/env python3
"""
Minimal smoke checks (non-invasive, CI-friendly):
- Validate cloud_config.json structure and feature flags exist with safe defaults.
This script intentionally avoids importing FreeCAD or hitting external services.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "cloud_config.json"

REQUIRED_TOP_LEVEL = [
    "cloud_api_url",
    "cloud_api_key",
    "dfm_endpoint",
    "text_to_cad",
    "llm",
    "features",
]

REQUIRED_FEATURES = [
    "text_to_cad_enabled",
    "dfm_enabled",
    "learning_agent_enabled",
    "shadow_mode",
]


def fail(msg: str) -> None:
    print(f"SMOKE: FAIL - {msg}")
    sys.exit(1)


def ok(msg: str) -> None:
    print(f"SMOKE: OK - {msg}")


def main() -> None:
    if not CONFIG.exists():
        fail(f"Missing config: {CONFIG}")

    try:
        data = json.loads(CONFIG.read_text())
    except Exception as e:
        fail(f"cloud_config.json invalid JSON: {e}")

    # Check required keys
    for key in REQUIRED_TOP_LEVEL:
        if key not in data:
            fail(f"Missing top-level key '{key}' in cloud_config.json")
    ok("Found required top-level keys in cloud_config.json")

    # Validate features
    features = data.get("features", {})
    for key in REQUIRED_FEATURES:
        if key not in features:
            fail(f"Missing features flag '{key}' in cloud_config.json")
        if not isinstance(features[key], bool):
            fail(f"Feature '{key}' must be a boolean")
    ok("Feature flags present and boolean")

    # Enforce safe defaults
    if features.get("learning_agent_enabled"):
        fail("'learning_agent_enabled' must be false by default")
    ok("'learning_agent_enabled' default is false (safe)")

    print("SMOKE: PASS - minimal config checks succeeded")


if __name__ == "__main__":
    main()
