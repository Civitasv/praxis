from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from praxis.state import enable_state, load_state, mutate_latest_state, mutate_state


class LatestStateMutationTests(unittest.TestCase):
    def test_latest_mutation_uses_current_state_after_prior_revision_movement(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            mutate_state(root, 0, lambda state: {**state, "earlier": True})

            updated = mutate_latest_state(root, lambda state: {**state, "machine": "fresh"})

            self.assertEqual(updated["revision"], 2)
            self.assertTrue(updated["earlier"])
            self.assertEqual(updated["machine"], "fresh")

    def test_latest_mutation_advances_revision_exactly_once_when_changed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)

            updated = mutate_latest_state(root, lambda state: {**state, "machine": 1})

            self.assertEqual(updated["revision"], 1)
            self.assertEqual(load_state(root)["revision"], 1)

    def test_latest_mutation_does_not_write_or_advance_revision_for_noop(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            original = enable_state(root)
            state_path = root / ".praxis" / "state.json"
            before = state_path.read_bytes()

            with patch("praxis.state._atomic_write_state", side_effect=AssertionError("must not write")):
                unchanged = mutate_latest_state(root, lambda state: None)

            self.assertEqual(unchanged, original)
            self.assertEqual(state_path.read_bytes(), before)
            self.assertEqual(load_state(root)["revision"], 0)


if __name__ == "__main__":
    unittest.main()
