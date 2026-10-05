from pathlib import Path
import tempfile
import unittest

from praxis.decisions import (
    create_decision,
    get_decision,
    record_implementation,
    record_verification,
    select_decision,
    supersede_decision,
)
from praxis.state import enable_state
from praxis.tasks import create_task


class VerifiedSupersedeTests(unittest.TestCase):
    def test_verified_decision_can_be_superseded_by_later_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            task_id, _ = create_task(root, 0, host="codex")
            old_id, _ = create_decision(root, task_id, "engineering", "Old", "old context")
            new_id, _ = create_decision(root, task_id, "engineering", "New", "new context")
            select_decision(root, old_id, 0, "Old choice")
            record_implementation(root, old_id, 1, "Old implementation")
            verified = record_verification(root, old_id, 2, "Old verification")
            self.assertEqual(get_decision(verified, old_id)["status"], "verified")

            superseded = supersede_decision(root, old_id, 3, new_id)
            record = get_decision(superseded, old_id)
            self.assertEqual(record["status"], "superseded")
            self.assertEqual(record["superseding_decision_id"], new_id)
            self.assertEqual(record["revision"], 4)


if __name__ == "__main__":
    unittest.main()
