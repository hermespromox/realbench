from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "public" / "runs"

EXPECTED_MODELS = {
    "grok-4.6": "x-ai/grok-4.6",
    "gpt-5.6-luna": "openai/gpt-5.6-luna",
    "gemini-3.8-flash": "google/gemini-3.8-flash",
    "glm-5.3-flash": "z-ai/glm-5.3-flash",
    "hy4-preview": "tencent/hy4-preview",
    "deepseek-v4-flash-0731": "deepseek/deepseek-v4-flash-0731",
    "kimi-k3": "moonshotai/kimi-k3",
    "gpt-5.6-sol": "openai/gpt-5.6-sol",
    "muse-spark-1.3": "meta/muse-spark-1.3",
    "gemma-4-31b-it": "google/gemma-4-31b-it",
}


class BenchmarkConfigurationTests(unittest.TestCase):
    def test_all_requested_models_are_registered_without_explicit_token_cap(self) -> None:
        import sys

        sys.path.insert(0, str(ROOT / "scripts"))
        import generate_benchmark

        self.assertEqual(EXPECTED_MODELS, {slug: item["id"] for slug, item in generate_benchmark.MODELS.items()})
        source = (ROOT / "scripts" / "generate_benchmark.py").read_text(encoding="utf-8")
        self.assertNotIn('"max_tokens"', source)


    def test_svg_namespace_uri_is_not_an_external_resource(self) -> None:
        import sys

        sys.path.insert(0, str(ROOT / "scripts"))
        import generate_benchmark

        html = (
            "<!DOCTYPE html><html><body>"
            '<svg xmlns="http://www.w3.org/2000/svg"><rect/></svg>'
            "</body></html>"
        )
        self.assertTrue(generate_benchmark.static_metrics(html)["self_contained"])


class GeneratedOutputIntegrityTests(unittest.TestCase):
    def test_all_benchmark_outputs_are_complete_html_documents(self) -> None:
        failures: list[str] = []
        files = sorted(RUNS.glob("*/*.html"))
        self.assertEqual(len(EXPECTED_MODELS) * 7, len(files))
        for path in files:
            text = path.read_text(encoding="utf-8")
            low = text.lower().rstrip()
            if "<!doctype html" not in low or "</html>" not in low:
                failures.append(f"{path.relative_to(ROOT)}: incomplete HTML document")
            if text.count("<script") != text.count("</script>"):
                failures.append(f"{path.relative_to(ROOT)}: unbalanced script tags")
        self.assertFalse(failures, "\n" + "\n".join(failures))

    def test_inline_js_parse_state_matches_manifest(self) -> None:
        """JS parse failures are legitimate benchmark results when the
        document itself is complete; the manifest must report them accurately."""
        import json
        import sys

        sys.path.insert(0, str(ROOT / "scripts"))
        from rescore_metrics import js_parses

        manifest = json.loads((ROOT / "src" / "data" / "results.json").read_text(encoding="utf-8"))
        by_key = {(r["scenario"], r["model"]): r for r in manifest["results"]}
        mismatches: list[str] = []
        for path in sorted(RUNS.glob("*/*.html")):
            scenario, model = path.parent.name, path.stem
            actual = js_parses(path.read_text(encoding="utf-8"))
            entry = by_key.get((scenario, model))
            self.assertIsNotNone(entry, f"{scenario}/{model} missing from manifest")
            if entry["metrics"].get("js_parses") != actual:
                mismatches.append(f"{scenario}/{model}: manifest={entry['metrics'].get('js_parses')} actual={actual}")
        self.assertFalse(mismatches, "\n".join(mismatches))


if __name__ == "__main__":
    unittest.main()
