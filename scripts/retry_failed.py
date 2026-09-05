#!/usr/bin/env python3
"""Retry failed RealBench cells with a hard wall-clock deadline per attempt."""
from __future__ import annotations

import concurrent.futures
import json
import os

from generate_benchmark import MANIFEST, MODELS, SCENARIOS, call_one, load_env

TARGETS = [
    ("city-traffic", "grok-4.6"),
    ("city-traffic", "kimi-k3"),
]
ATTEMPTS = 2
DEADLINE_SECONDS = 2400


def run_one(scenario_slug: str, model_slug: str, key: str) -> dict:
    job = (scenario_slug, SCENARIOS[scenario_slug], model_slug, MODELS[model_slug])
    last: dict | None = None
    for attempt in range(1, ATTEMPTS + 1):
        watchdog = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        future = watchdog.submit(call_one, job, key)
        try:
            result = future.result(timeout=DEADLINE_SECONDS)
            watchdog.shutdown(wait=False)
        except concurrent.futures.TimeoutError:
            # Do not block on the stalled socket; the 900s read timeout ends it.
            watchdog.shutdown(wait=False, cancel_futures=True)
            print(f"attempt {attempt} for {model_slug}/{scenario_slug} exceeded {DEADLINE_SECONDS}s", flush=True)
            continue
        last = result
        if result["status"] == "ok":
            result["attempt"] = attempt
            if attempt > 1:
                result["repaired"] = True
                result["repair_reason"] = f"Regenerated after {attempt - 1} failed/empty attempt(s)"
            return result
        print(f"attempt {attempt} failed: {result['error']}", flush=True)
    assert last is not None
    last["attempt"] = ATTEMPTS
    return last


def main() -> None:
    load_env()
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise SystemExit("OPENROUTER_API_KEY is missing")

    results: list[dict] = []
    all_ok = True
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(2, len(TARGETS))) as pool:
        futures = {
            pool.submit(run_one, scenario_slug, model_slug, key): (scenario_slug, model_slug)
            for scenario_slug, model_slug in TARGETS
        }
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            results.append(result)
            if result["status"] != "ok":
                all_ok = False

    # Re-read immediately before merge so a long generation cannot clobber
    # concurrent manifest updates.
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    existing = {(r["scenario"], r["model"]): i for i, r in enumerate(manifest["results"])}
    for result in results:
        key_pair = (result["scenario"], result["model"])
        position = existing.get(key_pair)
        if position is None:
            existing[key_pair] = len(manifest["results"])
            manifest["results"].append(result)
        else:
            manifest["results"][position] = result
    manifest["results"].sort(
        key=lambda r: (list(SCENARIOS).index(r["scenario"]), list(MODELS).index(r["model"]))
    )
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    if not all_ok:
        raise SystemExit("Some targets still failed")
    print("Retry merged into manifest")


if __name__ == "__main__":
    main()
