"""Reference relevance, applicability, access, and context-budget boundaries."""

import copy
import tempfile
import unittest
from pathlib import Path

from retrieval import ReferenceIndex, load_references, source_context


class RetrievalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "references.sqlite3"
        self.documents = load_references()

    def tearDown(self):
        self.temp.cleanup()

    def test_known_model_retrieves_applicable_fan_guidance(self):
        index = ReferenceIndex(self.path, self.documents)
        results = index.search("Fan remains off as temperature rises from a cold start", model="raspberry-pi-5")
        self.assertEqual(results[0]["id"], "RP-PI5-FAN")
        self.assertNotIn("RP-PI3-SOFT", {d["id"] for d in results})

    def test_revision_beats_upload_recency_and_missing_revision_abstains(self):
        a = dict(self.documents[0], id="TEST-A", models=["controller"], revision="A", uploaded_at="2026-09-08",
                 title="E14 remedy", text="E14 requires a replacement fan.", keywords="E14 diagnostic review")
        b = dict(a, id="TEST-B", revision="B", uploaded_at="2026-08-01", text="E14 is a clock warning; request diagnostic review.")
        obsolete = dict(b, id="TEST-OLD", status="superseded")
        index = ReferenceIndex(self.path, [a, b, obsolete])
        result = index.search("E14 diagnostic review", model="controller", revision="B")
        self.assertEqual([d["id"] for d in result], ["TEST-B"])
        self.assertFalse(index.search("E14 diagnostic review", model="controller"))

    def test_access_and_revocation_filter_before_top_k(self):
        public = dict(self.documents[0], id="PUBLIC", text="thermal fan", keywords="", title="Guide")
        private = dict(public, id="PRIVATE", owner_id="alice", text="thermal fan temperature clock warning",
                       keywords="temperature clock warning", title="temperature clock warning")
        revoked = dict(private, id="REVOKED", owner_id=None, status="revoked")
        index = ReferenceIndex(self.path, [public, private, revoked])
        for method in ("bm25", "overlap"):
            with self.subTest(method=method):
                result = index.search("thermal fan temperature clock warning", model="raspberry-pi-4", actor="bob", limit=1, method=method)
                self.assertEqual([d["id"] for d in result], ["PUBLIC"])
                own = index.search("thermal fan temperature clock warning", model="raspberry-pi-4", actor="alice", limit=4, method=method)
                self.assertIn("PRIVATE", {d["id"] for d in own})
                self.assertNotIn("REVOKED", {d["id"] for d in own})

    def test_unreviewed_media_and_conflicting_models_cannot_establish_context(self):
        self.assertEqual(source_context([{"text": "Raspberry Pi 5 fan", "origin": "groq_image"}])["status"], "unknown_model")
        self.assertEqual(source_context([{"text": "Raspberry Pi 4 or Raspberry Pi 5"}])["status"], "ambiguous_model")
        self.assertEqual(source_context([{"text": "Raspberry Pi 5", "evidence_role": "reference", "type": "reference"}])["status"], "unknown_model")
        self.assertEqual(source_context([{"text": "Raspberry Pi 5 revision b."}])["revision"], "B")
        self.assertEqual(source_context([{"text": "This might be a Raspberry Pi 5."}])["status"], "unknown_model")
        self.assertEqual(source_context([{"text": "This is not a Raspberry Pi 5."}])["status"], "unknown_model")

    def test_context_budget_preserves_whole_sources_without_truncating_guidance(self):
        index = ReferenceIndex(self.path, self.documents)
        sources = [{"id": "N1", "text": "Gateway uses a Raspberry Pi 5; fan remains off during warm-up.", "origin": "user"}]
        original = copy.deepcopy(sources)
        enriched, trace = index.enrich(sources, "alice", max_chars=len(sources[0]["text"]) + 1)
        self.assertEqual(enriched, original)
        self.assertEqual(trace["status"], "context_budget")
        self.assertTrue(trace["context_budget_excluded"])
        enriched, trace = index.enrich(sources, "alice")
        self.assertEqual(enriched[0], original[0])
        self.assertTrue(all(s["evidence_role"] == "reference" for s in enriched[1:]))
        self.assertTrue(all(s["reference_version"] and s["reference_sha256"] for s in enriched[1:]))

    def test_query_syntax_is_data_and_unknown_topics_do_not_return_documents(self):
        index = ReferenceIndex(self.path, self.documents)
        self.assertFalse(index.search('" OR title:ZZZXQ* NOT ( NEAR )', model="raspberry-pi-5"))
        self.assertFalse(index.search("hydraulic zephyr xyz987", model="raspberry-pi-5"))
        self.assertFalse(index.search("fan temperature", model=None))
        self.assertFalse(index.search("Fan remains off below a temperature of 50 degrees", model="raspberry-pi-4"))

    def test_changed_corpus_rebuilds_index_and_removes_revoked_content(self):
        index = ReferenceIndex(self.path, self.documents)
        self.assertTrue(index.search("fan remains off", model="raspberry-pi-5"))
        changed = [dict(d, status="revoked") for d in self.documents]
        index = ReferenceIndex(self.path, changed)
        self.assertFalse(index.search("fan remains off", model="raspberry-pi-5"))
        with self.assertRaisesRegex(ValueError, "unique"):
            ReferenceIndex(self.path, [self.documents[0], self.documents[0]])


if __name__ == "__main__":
    unittest.main()
