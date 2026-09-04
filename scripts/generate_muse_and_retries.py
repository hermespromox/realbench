#!/usr/bin/env python3
"""Generate Muse Spark 1.3 on all scenarios and retry remaining failed cells."""
from __future__ import annotations

import concurrent.futures
import json
import os

from generate_benchmark import MANIFEST, MODELS, SCENARIOS, call_one, load_env

NEW_MODEL = "muse-spark-1.3"
RETRY_TARGETS = [
    ("city-traffic", "kimi-k3"),
    ("factory", "deepseek-v4-flash-0731"),
]
DEADLINE_SECONDS = 2400
ATTEMPTS = 2


def call_with_deadline(job, key: str) -> dict:
    scenario_slug, scenario, model_slug, model = job
    last = None
    for attempt in range(1, ATTEMPTS + 1):
        watchdog = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        future = watchdog.submit(call_one, job, key)
        try:
            result = future.result(timeout=DEADLINE_SECONDS)
            watchdog.shutdown(wait=False)
        except concurrent.futures.TimeoutError:
            watchdog.shutdown(wait=False, cancel_futures=True)
            print(f"timeout attempt {attempt}: {model_slug}/{scenario_slug}", flush=True)
            continue
        last = result
        if result["status"] == "ok":
            result["attempt"] = attempt
            if attempt > 1:
                result["repaired"] = True
                result["repair_reason"] = "Regenerated after a failed or empty attempt"
            return result
        print(f"failed attempt {attempt}: {model_slug}/{scenario_slug}: {result['error']}", flush=True)
    assert last is not None
    last["attempt"] = ATTEMPTS
    return last


def main() -> None:
    load_env()
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise SystemExit("OPENROUTER_API_KEY is missing")

    jobs = [
        (scenario_slug, scenario, NEW_MODEL, MODELS[NEW_MODEL])
        for scenario_slug, scenario in SCENARIOS.items()
    ] + [
        (scenario_slug, SCENARIOS[scenario_slug], model_slug, MODELS[model_slug])
        for scenario_slug, model_slug in RETRY_TARGETS
    ]

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(call_with_deadline, job, key) for job in jobs]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    index = {(r["scenario"], r["model"]): i for i, r in enumerate(manifest["results"])}
    for result in results:
        position = index.get((result["scenario"], result["model"]))
        if position is None:
            manifest["results"].append(result)
            index[(result["scenario"], result["model"])] = len(manifest["results"]) - 1
        else:
            manifest["results"][position] = result
    manifest["models"] = MODELS
    manifest["scenarios"] = SCENARIOS
    manifest["results"].sort(
        key=lambda r: (list(SCENARIOS).index(r["scenario"]), list(MODELS).index(r["model"]))
    )
    manifest["generated_at"] = manifest.get("generated_at")
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    failures = [r for r in results if r["status"] != "ok"]
    print(f"Completed {len(results) - len(failures)}/{len(results)}")
    if failures:
        print("Failures:", [(r["model"], r["scenario"], r["error"]) for r in failures])
        raise SystemExit(1)


if __name__ == "__main__":
    main()
