#!/usr/bin/env python3
"""Generate the Super Mario Bros scene for every RealBench model.

Writes HTML immediately and stores per-model JSON under
benchmark/pending/super-mario-bros/. The main results.json is merged only
after all jobs finish, by re-reading the manifest at merge time.
"""
from __future__ import annotations

import concurrent.futures
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from generate_benchmark import MANIFEST, MODELS, SCENARIOS, call_one, load_env

SCENARIO = "super-mario-bros"
PENDING = Path(__file__).resolve().parents[1] / "benchmark" / "pending" / SCENARIO
ATTEMPTS = 2
DEADLINE_SECONDS = 2400
MAX_WORKERS = 4


def run_one(model_slug: str, key: str) -> dict:
    job = (SCENARIO, SCENARIOS[SCENARIO], model_slug, MODELS[model_slug])
    last: dict | None = None
    for attempt in range(1, ATTEMPTS + 1):
        watchdog = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        future = watchdog.submit(call_one, job, key)
        try:
            result = future.result(timeout=DEADLINE_SECONDS)
            watchdog.shutdown(wait=False)
        except concurrent.futures.TimeoutError:
            watchdog.shutdown(wait=False, cancel_futures=True)
            print(f"attempt {attempt} for {model_slug}/{SCENARIO} exceeded {DEADLINE_SECONDS}s", flush=True)
            continue
        last = result
        result["attempt"] = attempt
        PENDING.mkdir(parents=True, exist_ok=True)
        (PENDING / f"{model_slug}.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        if result["status"] == "ok":
            if attempt > 1:
                result["repaired"] = True
                result["repair_reason"] = f"Regenerated after {attempt - 1} failed/empty attempt(s)"
                (PENDING / f"{model_slug}.json").write_text(
                    json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
                )
            return result
        print(f"attempt {attempt} failed for {model_slug}: {result['error']}", flush=True)
    assert last is not None
    last["attempt"] = ATTEMPTS
    return last


def merge(results: list[dict]) -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest["models"] = MODELS
    manifest["scenarios"] = SCENARIOS
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
    manifest["generated_at"] = datetime.now(timezone.utc).isoformat()
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    load_env()
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise SystemExit("OPENROUTER_API_KEY is missing")
    if SCENARIO not in SCENARIOS:
        raise SystemExit(f"missing scenario {SCENARIO}")

    PENDING.mkdir(parents=True, exist_ok=True)
    results: list[dict] = []
    failures: list[dict] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(run_one, slug, key): slug for slug in MODELS}
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            results.append(result)
            if result["status"] != "ok":
                failures.append(result)

    merge(results)
    print(f"Super Mario Bros: {len(results) - len(failures)}/{len(results)} successful")
    if failures:
        print("Failures:", [(r["model"], r["error"]) for r in failures])
        raise SystemExit(1)


if __name__ == "__main__":
    main()
