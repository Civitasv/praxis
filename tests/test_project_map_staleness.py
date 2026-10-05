import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from praxis.fingerprints import EvidenceError
from praxis.project_map import get_project_model, refresh_staleness, upsert_section
from praxis.state import enable_state, load_state, mutate_state


class ProjectMapStalenessTests(unittest.TestCase):
    def make_source(self, root: Path, relative: str, content: str) -> Path:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def test_changed_file_marks_only_dependent_section_stale_without_changing_section_revision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            auth = self.make_source(root, "auth.py", "auth-v1")
            self.make_source(root, "billing.py", "billing-v1")
            upsert_section(root, "auth", "Auth", "auth model", ["auth.py"])
            before = upsert_section(root, "billing", "Billing", "billing model", ["billing.py"])
            before_model = get_project_model(before)

            auth.write_text("auth-v2", encoding="utf-8")
            after = refresh_staleness(root)
            model = get_project_model(after)

            self.assertEqual(model["revision"], before_model["revision"] + 1)
            self.assertEqual(model["sections"]["auth"]["status"], "stale")
            self.assertEqual(
                model["sections"]["auth"]["stale_reasons"],
                [{"path": "auth.py", "reason": "changed"}],
            )
            self.assertEqual(
                model["sections"]["auth"]["revision"],
                before_model["sections"]["auth"]["revision"],
            )
            self.assertEqual(model["sections"]["billing"], before_model["sections"]["billing"])

    def test_missing_file_records_missing_reason(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            source = self.make_source(root, "a.py", "a")
            upsert_section(root, "a", "A", "a model", ["a.py"])
            source.unlink()

            state = refresh_staleness(root)

            self.assertEqual(
                get_project_model(state)["sections"]["a"]["stale_reasons"],
                [{"path": "a.py", "reason": "missing"}],
            )

    def test_shared_changed_evidence_stales_every_dependent_section(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            shared = self.make_source(root, "shared.py", "v1")
            upsert_section(root, "a", "A", "a model", ["shared.py"])
            upsert_section(root, "b", "B", "b model", ["shared.py"])
            shared.write_text("v2", encoding="utf-8")

            state = refresh_staleness(root)
            sections = get_project_model(state)["sections"]

            self.assertEqual(sections["a"]["status"], "stale")
            self.assertEqual(sections["b"]["status"], "stale")

    def test_unknown_section_with_no_evidence_remains_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            before = upsert_section(root, "unknowns", "Unknowns", "not verified", [])

            after = refresh_staleness(root)

            self.assertEqual(after, before)
            self.assertEqual(get_project_model(after)["sections"]["unknowns"]["status"], "unknown")

    def test_repeated_identical_scan_is_a_true_noop(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            source = self.make_source(root, "a.py", "v1")
            upsert_section(root, "a", "A", "a model", ["a.py"])
            source.write_text("v2", encoding="utf-8")
            first = refresh_staleness(root)
            state_path = root / ".praxis" / "state.json"
            before_bytes = state_path.read_bytes()
            before_model = get_project_model(first)

            with patch("praxis.state._atomic_write_state", side_effect=AssertionError("no-op scan must not write")):
                second = refresh_staleness(root)

            self.assertEqual(second["revision"], first["revision"])
            self.assertEqual(get_project_model(second)["revision"], before_model["revision"])
            self.assertEqual(
                get_project_model(second)["sections"]["a"]["revision"],
                before_model["sections"]["a"]["revision"],
            )
            self.assertEqual(state_path.read_bytes(), before_bytes)

    def test_unsafe_stored_evidence_is_marked_stale_instead_of_followed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            root = Path(tmp)
            enable_state(root)
            external = Path(outside) / "external.py"
            external.write_text("outside", encoding="utf-8")
            digest = hashlib.sha256(external.read_bytes()).hexdigest()
            seeded = mutate_state(
                root,
                0,
                lambda state: {
                    **state,
                    "project_model": {
                        "revision": 0,
                        "sections": {
                            "unsafe": {
                                "title": "Unsafe",
                                "revision": 0,
                                "status": "verified",
                                "content": "seeded model",
                                "evidence": [{"path": "../external.py", "sha256": digest}],
                                "stale_reasons": [],
                            }
                        },
                    },
                },
            )
            self.assertIn("project_model", seeded)

            state = refresh_staleness(root)

            self.assertEqual(
                get_project_model(state)["sections"]["unsafe"]["stale_reasons"],
                [{"path": "../external.py", "reason": "unsafe"}],
            )

    def test_unreadable_evidence_records_unreadable_reason(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            self.make_source(root, "a.py", "a")
            upsert_section(root, "a", "A", "a model", ["a.py"])

            with patch(
                "praxis.project_map.fingerprint_file",
                side_effect=EvidenceError("unreadable", "a.py", "denied"),
            ):
                state = refresh_staleness(root)

            self.assertEqual(
                get_project_model(state)["sections"]["a"]["stale_reasons"],
                [{"path": "a.py", "reason": "unreadable"}],
            )


if __name__ == "__main__":
    unittest.main()
