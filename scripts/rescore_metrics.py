#!/usr/bin/env python3
"""Recompute deterministic metrics for every published artifact without regenerating."""
from __future__ import annotations

import json

from generate_benchmark import MANIFEST, OUT, static_metrics


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    updated = 0
    for result in manifest["results"]:
        path = OUT / result["scenario"] / f"{result['model']}.html"
        if not path.exists() or result["status"] != "ok":
            continue
        metrics = static_metrics(path.read_text(encoding="utf-8"))
        if metrics != result["metrics"]:
            result["metrics"] = metrics
            updated += 1
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Recomputed metrics: {updated} results updated")


if __name__ == "__main__":
    main()
