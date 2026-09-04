#!/usr/bin/env python3
"""Generate the RealBench one-shot frontend benchmark through OpenRouter."""
from __future__ import annotations

import concurrent.futures
import json
import os
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "public" / "runs"
RAW = ROOT / "benchmark" / "raw"
MANIFEST = ROOT / "src" / "data" / "results.json"

MODELS = {
    "grok-4.6": {"id": "x-ai/grok-4.6", "name": "Grok 4.6", "vendor": "xAI", "color": "#111111"},
    "gpt-5.6-luna": {"id": "openai/gpt-5.6-luna", "name": "GPT-5.6 Luna", "vendor": "OpenAI", "color": "#10a37f"},
    "gemini-3.8-flash": {"id": "google/gemini-3.8-flash", "name": "Gemini 3.8 Flash", "vendor": "Google", "color": "#4285f4"},
    "glm-5.3-flash": {"id": "z-ai/glm-5.3-flash", "name": "GLM 5.3 Flash", "vendor": "Z.ai", "color": "#7c3aed"},
    "hy4-preview": {"id": "tencent/hy4-preview", "name": "HY 4 Preview", "vendor": "Tencent", "color": "#00a4ef"},
    "deepseek-v4-flash-0731": {"id": "deepseek/deepseek-v4-flash-0731", "name": "DeepSeek V4 Flash 0731", "vendor": "DeepSeek", "color": "#4d6bfe"},
    "kimi-k3": {"id": "moonshotai/kimi-k3", "name": "Kimi K3", "vendor": "Moonshot AI", "color": "#111827"},
    "gpt-5.6-sol": {"id": "openai/gpt-5.6-sol", "name": "GPT-5.6 Sol", "vendor": "OpenAI", "color": "#0f9d7a"},
}

SCENARIOS = {
    "solar-system": {
        "name": "Solar System",
        "icon": "◉",
        "capability": "Geometry / depth",
        "prompt": "Create a single self-contained HTML file showing a cinematic animated solar system. The Sun is centered, 8 planets orbit around it at different speeds, moons orbit selected planets, orbit paths are subtly visible, stars slowly drift in the background, and the whole scene has a sense of depth. The animation must run continuously and loop naturally. Use only HTML, CSS, SVG, Canvas and vanilla JavaScript. No external libraries, images, fonts or network requests.",
    },
    "city-traffic": {
        "name": "City Traffic",
        "icon": "▦",
        "capability": "Complexity / agents",
        "prompt": "Create a self-contained HTML animation showing a stylized modern city from a top-down perspective. Cars continuously move through streets and intersections, traffic lights change automatically, pedestrians cross at selected intersections, building lights subtly animate, and traffic density changes over time. The scene should feel alive and continuously animated. No interaction. No external libraries or assets.",
    },
    "aquarium": {
        "name": "Living Aquarium",
        "icon": "≈",
        "capability": "Organic motion",
        "prompt": "Create a self-contained animated underwater ecosystem in a single HTML file. Show at least 25 fish moving independently, several schools of small fish, jellyfish drifting slowly, bubbles rising, seaweed moving with underwater currents, floating particles, and animated light rays coming from the surface. Movements should feel organic rather than synchronized. The animation should loop seamlessly. No interaction and no external assets.",
    },
    "rube-goldberg": {
        "name": "Rube Goldberg",
        "icon": "↝",
        "capability": "Visual causality",
        "prompt": "Create a self-contained HTML animation of an elaborate Rube Goldberg machine. A ball rolls down a ramp, knocks over dominoes, triggers a lever, releases another ball, spins a wheel, launches an object through the air and finally rings a bell. The entire chain reaction must be clearly understandable visually and restart automatically after completing. No user interaction. No external libraries or assets.",
    },
    "factory": {
        "name": "Future Factory",
        "icon": "⌬",
        "capability": "System coordination",
        "prompt": "Create a self-contained HTML animation showing a futuristic automated factory from an isometric perspective. Conveyor belts continuously move products through the factory. Robotic arms pick up and place objects, machines stamp and assemble components, autonomous carts move between stations, indicator lights blink and completed products accumulate before leaving the factory. The entire workflow should run continuously as a coherent production process. No interaction and no external libraries or assets.",
    },
}

SYSTEM = """You are participating in RealBench, a one-shot frontend animation benchmark.
Return ONLY the complete self-contained HTML document, starting with <!DOCTYPE html>.
Do not use markdown fences or explanations. Do not use external assets, libraries, fonts, URLs, fetch, or network requests.
The animation must start automatically, run continuously for at least 15 seconds, and require no user input.
Use the full viewport and prioritize visual polish, coherent motion, density, and technical correctness.
This is one-shot: your output is displayed exactly as generated and will not be repaired."""


def load_env() -> None:
    for path in [Path.home() / ".hermes" / ".env", ROOT / ".env.local"]:
        if not path.exists():
            continue
        for line in path.read_text(errors="ignore").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            value = value.strip().strip("'\"")
            os.environ.setdefault(key.strip(), value)


def extract_html(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:html)?\s*", "", text, flags=re.I)
        text = re.sub(r"\s*```$", "", text)
    start = text.lower().find("<!doctype html")
    if start < 0:
        start = text.lower().find("<html")
    return text[start:].strip() if start >= 0 else text


def static_metrics(html: str) -> dict:
    low = html.lower()
    # XML namespace URIs (e.g. SVG xmlns="http://www.w3.org/2000/svg") are
    # identifiers, never network fetches; strip them before the check.
    scan = re.sub(r"xmlns(:[a-z0-9-]+)?\s*=\s*(\"[^\"]*\"|'[^']*')", "", low)
    external_patterns = ["https://", "http://", "fetch(", "@import", "<script src=", "<link href="]
    return {
        "valid_html": "<html" in low and "</html>" in low,
        "self_contained": not any(p in scan for p in external_patterns),
        "bytes": len(html.encode("utf-8")),
        "uses_canvas": "<canvas" in low,
        "uses_svg": "<svg" in low,
        "uses_css_animation": "@keyframes" in low,
        "uses_raf": "requestanimationframe" in low,
        "animation_signals": sum(low.count(x) for x in ["@keyframes", "requestanimationframe", "setinterval", "animate("]),
        "dom_nodes_approx": len(re.findall(r"<[a-z][a-z0-9-]*(?:\s|>)", low)),
    }


def call_one(item: tuple[str, dict, str, dict], api_key: str) -> dict:
    scenario_slug, scenario, model_slug, model = item
    out_path = OUT / scenario_slug / f"{model_slug}.html"
    raw_path = RAW / scenario_slug / f"{model_slug}.txt"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.parent.mkdir(parents=True, exist_ok=True)

    body = {
        "model": model["id"],
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": scenario["prompt"]},
        ],
        "temperature": 0.7,
    }
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://realbench-delta.vercel.app",
            "X-Title": "RealBench",
        },
        method="POST",
    )
    started = time.time()
    status = "ok"
    error = None
    usage = {}
    provider = None
    raw_text = ""
    try:
        # Hard deadline so a stalled route cannot hang the run for 30 minutes.
        with urllib.request.urlopen(req, timeout=900) as response:
            payload = json.loads(response.read())
        raw_text = payload["choices"][0]["message"].get("content") or ""
        usage = payload.get("usage") or {}
        provider = payload.get("provider")
        if not raw_text:
            raise ValueError("Model returned empty content")
    except Exception as exc:
        status = "error"
        error = str(exc)
        if isinstance(exc, urllib.error.HTTPError):
            try:
                error += ": " + exc.read().decode()[:600]
            except Exception:
                pass

    elapsed = round(time.time() - started, 2)
    html = extract_html(raw_text) if raw_text else f"<!DOCTYPE html><html><body style='background:#111;color:white;font-family:sans-serif;padding:40px'><h1>Generation failed</h1><pre>{error}</pre></body></html>"
    raw_path.write_text(raw_text or error or "Unknown error")
    out_path.write_text(html)
    metrics = static_metrics(html)
    print(f"[{status}] {model_slug} / {scenario_slug} — {elapsed}s, {metrics['bytes']} bytes", flush=True)
    return {
        "scenario": scenario_slug,
        "model": model_slug,
        "status": status,
        "error": error,
        "duration_seconds": elapsed,
        "provider": provider,
        "usage": usage,
        "metrics": metrics,
        "path": f"/runs/{scenario_slug}/{model_slug}.html",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def main() -> None:
    load_env()
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise SystemExit("OPENROUTER_API_KEY is missing")
    OUT.mkdir(parents=True, exist_ok=True)
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    jobs = [(ss, s, ms, m) for ss, s in SCENARIOS.items() for ms, m in MODELS.items()]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(call_one, job, key) for job in jobs]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    results.sort(key=lambda x: (list(SCENARIOS).index(x["scenario"]), list(MODELS).index(x["model"])))
    manifest = {
        "name": "RealBench",
        "methodology": "One-shot, same prompt, no repair, self-contained HTML, no external assets",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "models": MODELS,
        "scenarios": SCENARIOS,
        "results": results,
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    failures = [r for r in results if r["status"] != "ok"]
    print(f"Done: {len(results)-len(failures)}/{len(results)} successful")
    if failures:
        print("Failures:", [(r["model"], r["scenario"], r["error"]) for r in failures])


if __name__ == "__main__":
    main()
