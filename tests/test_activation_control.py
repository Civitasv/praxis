from pathlib import Path
import tempfile
import unittest

from praxis.state import disable_state, enable_state, load_state


class PraxisActivationControlTests(unittest.TestCase):
    def test_disable_uninitialized_project_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertIsNone(disable_state(root))
            self.assertFalse((root / ".praxis").exists())

    def test_enable_disable_enable_without_revision_round_trips(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = enable_state(root)
            self.assertTrue(first["enabled"])
            self.assertEqual(first["revision"], 0)

            disabled = disable_state(root)
            self.assertFalse(disabled["enabled"])
            self.assertEqual(disabled["revision"], 1)

            enabled = enable_state(root)
            self.assertTrue(enabled["enabled"])
            self.assertEqual(enabled["revision"], 2)
            self.assertEqual(load_state(root), enabled)


if __name__ == "__main__":
    unittest.main()
