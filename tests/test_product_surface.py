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

    def test_published_prompt_is_not_rendered(self) -> None:
        arena = (ROOT / "src/components/Arena.tsx").read_text(encoding="utf-8")
        challenge = (ROOT / "src/app/challenges/[slug]/page.tsx").read_text(encoding="utf-8")
        self.assertNotIn("selected.prompt", arena)
        self.assertNotIn("scenario.prompt", challenge)
        self.assertNotIn("showPrompt", arena)

    def test_votes_use_authenticated_blob_get(self) -> None:
        votes = (ROOT / "src/lib/votes.ts").read_text(encoding="utf-8")
        self.assertIn('from "@vercel/blob"', votes)
        self.assertIn("get(BLOB_PATH", votes)
        self.assertIn('access: "private"', votes)
        self.assertNotIn("blob.vercel-storage.com", votes)

    def test_canonical_site_url_is_benchviz(self) -> None:
        catalog = (ROOT / "src/lib/catalog.ts").read_text(encoding="utf-8")
        robots = (ROOT / "src/app/robots.ts").read_text(encoding="utf-8")
        self.assertIn('SITE_URL = "https://www.benchviz.com"', catalog)
        self.assertNotIn("realbench-delta.vercel.app", catalog)
        self.assertIn("SITE_URL", robots)
