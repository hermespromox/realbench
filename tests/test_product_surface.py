from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ProductSurfaceTests(unittest.TestCase):
    def test_vote_api_and_library_routes_exist(self) -> None:
        expected = [
            ROOT / "src/app/api/votes/route.ts",
            ROOT / "src/app/library/page.tsx",
            ROOT / "src/app/models/[slug]/page.tsx",
            ROOT / "src/app/challenges/[slug]/page.tsx",
            ROOT / "src/app/sitemap.ts",
            ROOT / "src/app/robots.ts",
        ]
        missing = [str(path.relative_to(ROOT)) for path in expected if not path.exists()]
        self.assertFalse(missing, "missing routes: " + ", ".join(missing))

    def test_ibm_tokens_are_present(self) -> None:
        css = (ROOT / "src/app/globals.css").read_text(encoding="utf-8")
        self.assertIn("#0f62fe", css)
        self.assertIn("#f4f4f4", css)
