#!/usr/bin/env python3
"""Generate only the five additional RealBench models and merge their results."""
from __future__ import annotations

import concurrent.futures
import json
import os
from datetime import datetime, timezone

from generate_benchmark import MANIFEST, MODELS, OUT, SCENARIOS, call_one, load_env

NEW_MODEL_SLUGS = [
    "glm-5.3-flash",
    "hy4-preview",
    "deepseek-v4-flash-0731",
    "kimi-k3",
    "gpt-5.6-sol",
]


def main() -> None:
    load_env()
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise SystemExit("OPENROUTER_API_KEY is missing")

    OUT.mkdir(parents=True, exist_ok=True)
    jobs = [
        (scenario_slug, scenario, model_slug, MODELS[model_slug])
        for scenario_slug, scenario in SCENARIOS.items()
        for model_slug in NEW_MODEL_SLUGS
    ]
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        futures = [pool.submit(call_one, job, key) for job in jobs]
        new_results = [future.result() for future in concurrent.futures.as_completed(futures)]

    if MANIFEST.exists():
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    else:
        manifest = {"name": "RealBench", "results": []}

    new_keys = {(result["scenario"], result["model"]) for result in new_results}
    preserved = [
        result for result in manifest.get("results", [])
        if (result["scenario"], result["model"]) not in new_keys
    ]
    combined = preserved + new_results
    combined.sort(
        key=lambda result: (
            list(SCENARIOS).index(result["scenario"]),
            list(MODELS).index(result["model"]),
        )
    )
    manifest.update({
        "name": "RealBench",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "models": MODELS,
        "scenarios": SCENARIOS,
        "results": combined,
    })
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    failures = [result for result in new_results if result["status"] != "ok"]
    print(f"Additional models: {len(new_results) - len(failures)}/{len(new_results)} successful")
    if failures:
        print("Failures:", [(r["model"], r["scenario"], r["error"]) for r in failures])
        raise SystemExit(1)


if __name__ == "__main__":
    main()
