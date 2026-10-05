from pathlib import Path
import tempfile
import unittest

from praxis.locking import LockTimeoutError, StateLock


class StateLockTests(unittest.TestCase):
    def test_second_writer_times_out_and_lock_is_reusable_after_release(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with StateLock(root, timeout=0.1, poll_interval=0.005):
                with self.assertRaises(LockTimeoutError):
                    with StateLock(root, timeout=0.02, poll_interval=0.005):
                        self.fail("second writer must not acquire lock")
            with StateLock(root, timeout=0.02, poll_interval=0.005):
                self.assertTrue((root / ".praxis" / ".write-lock").is_dir())
        self.assertFalse((root / ".praxis" / ".write-lock").exists())


if __name__ == "__main__":
    unittest.main()
