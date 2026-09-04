#!/usr/bin/env python3
"""Retry the remaining failed RealBench cells and update the manifest in place."""
from __future__ import annotations

import json
import os

from generate_benchmark import MANIFEST, MODELS, SCENARIOS, call_one, load_env

TARGETS = [
    ("city-traffic", "kimi-k3"),
]


def main() -> None:
    load_env()
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise SystemExit("OPENROUTER_API_KEY is missing")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for scenario_slug, model_slug in TARGETS:
        result = call_one((scenario_slug, SCENARIOS[scenario_slug], model_slug, MODELS[model_slug]), key)
        if result["status"] != "ok":
            raise SystemExit(f"Retry still failed: {result['error']}")
        result["attempt"] = 2
        result["repaired"] = True
        result["repair_reason"] = "First request returned empty content; regenerated once"
        existing = {
            (r["scenario"], r["model"]): i for i, r in enumerate(manifest["results"])
        }
        position = existing.get((scenario_slug, model_slug))
        if position is None:
            manifest["results"].append(result)
        else:
            manifest["results"][position] = result
    manifest["results"].sort(
        key=lambda r: (list(SCENARIOS).index(r["scenario"]), list(MODELS).index(r["model"]))
    )
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Retry merged into manifest")


if __name__ == "__main__":
    main()
