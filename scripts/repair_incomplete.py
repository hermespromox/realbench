#!/usr/bin/env python3
"""Regenerate only truncated RealBench outputs and label them as repaired."""
from __future__ import annotations

import concurrent.futures
import json
import os
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from generate_benchmark import (
    MANIFEST,
    MODELS,
    OUT,
    ROOT,
    SCENARIOS,
    SYSTEM,
    extract_html,
    load_env,
    static_metrics,
)

TARGETS = [
    ("city-traffic", "gemini-3.8-flash"),
    ("factory", "grok-4.6"),
    ("factory", "gemini-3.8-flash"),
]
REPAIRS = ROOT / "benchmark" / "repairs"


def regenerate(target: tuple[str, str], api_key: str) -> dict:
    scenario_slug, model_slug = target
    scenario = SCENARIOS[scenario_slug]
    model = MODELS[model_slug]
    body = {
        "model": model["id"],
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": scenario["prompt"]},
        ],
        "temperature": 0.7,
    }
    request = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://www.benchviz.com",
            "X-Title": "RealBench repair run",
        },
        method="POST",
    )
    started = time.time()
    with urllib.request.urlopen(request, timeout=900) as response:
        payload = json.loads(response.read())
    choice = payload["choices"][0]
    raw = choice["message"].get("content") or ""
    finish_reason = choice.get("finish_reason")
    html = extract_html(raw)
    metrics = static_metrics(html)
    complete = metrics["valid_html"] and html.count("<script") == html.count("</script>")
    if not complete:
        raise RuntimeError(f"Repair is still incomplete (finish_reason={finish_reason}, bytes={metrics['bytes']})")

    repair_path = REPAIRS / scenario_slug / f"{model_slug}.txt"
    public_path = OUT / scenario_slug / f"{model_slug}.html"
    repair_path.parent.mkdir(parents=True, exist_ok=True)
    repair_path.write_text(raw, encoding="utf-8")
    public_path.write_text(html, encoding="utf-8")
    elapsed = round(time.time() - started, 2)
    print(f"REPAIRED {scenario_slug}/{model_slug}: {metrics['bytes']} bytes in {elapsed}s", flush=True)
    return {
        "scenario": scenario_slug,
        "model": model_slug,
        "duration_seconds": elapsed,
        "provider": payload.get("provider"),
        "usage": payload.get("usage") or {},
        "metrics": metrics,
        "finish_reason": finish_reason,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def main() -> None:
    load_env()
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise SystemExit("OPENROUTER_API_KEY missing")
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        repaired = list(pool.map(lambda t: regenerate(t, api_key), TARGETS))

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    by_key = {(r["scenario"], r["model"]): r for r in manifest["results"]}
    for item in repaired:
        result = by_key[(item["scenario"], item["model"])]
        result.update({
            "status": "ok",
            "error": None,
            "duration_seconds": item["duration_seconds"],
            "provider": item["provider"],
            "usage": item["usage"],
            "metrics": item["metrics"],
            "generated_at": item["generated_at"],
            "repaired": True,
            "attempt": 2,
            "repair_reason": "Original one-shot response was truncated at the output-token limit",
            "original_preserved_at": f"/benchmark/raw/{item['scenario']}/{item['model']}.txt",
        })
    manifest["repaired_at"] = datetime.now(timezone.utc).isoformat()
    manifest["methodology"] = "Same prompt; original one-shot responses archived. Truncated outputs regenerated once with a larger output budget and explicitly labeled repaired."
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
