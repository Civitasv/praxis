from pathlib import Path
import tempfile
import unittest

from praxis.decisions import UnknownTaskError, create_decision
from praxis.state import enable_state


class DecisionErrorTypeTests(unittest.TestCase):
    def test_unknown_task_has_dedicated_neutral_exception(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            with self.assertRaises(UnknownTaskError):
                create_decision(root, "task_deadbeef", "engineering", "Storage", "Choose storage")


if __name__ == "__main__":
    unittest.main()
