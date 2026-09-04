#!/usr/bin/env python3
"""Recompute deterministic metrics for every published artifact without regenerating."""
from __future__ import annotations

import json
import re
import subprocess
import tempfile
from pathlib import Path

from generate_benchmark import MANIFEST, OUT, static_metrics


def js_parses(text: str) -> bool:
    for script in re.findall(r"<script(?:\s[^>]*)?>(.*?)</script>", text, flags=re.I | re.S):
        with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8") as tmp:
            tmp.write(script)
            tmp.flush()
            if subprocess.run(["node", "--check", tmp.name], capture_output=True).returncode:
                return False
    return True


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    updated = 0
    for result in manifest["results"]:
        path = OUT / result["scenario"] / f"{result['model']}.html"
        if not path.exists() or result["status"] != "ok":
            continue
        text = path.read_text(encoding="utf-8")
        metrics = static_metrics(text)
        metrics["js_parses"] = js_parses(text)
        if metrics != result["metrics"]:
            result["metrics"] = metrics
            updated += 1
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Recomputed metrics: {updated} results updated")


if __name__ == "__main__":
    main()
