import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from praxis.state import FORMAT_VERSION, InvalidStateError, MalformedStateError, RevisionConflictError, StateWriteError, UnsupportedFormatError, enable_state, load_state, mutate_state, pause_state

class StateSchemaTests(unittest.TestCase):
    def test_absent_state_loads_none_without_creating_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); self.assertIsNone(load_state(root)); self.assertFalse((root/'.praxis').exists())
    def test_first_enable_initializes_format_one_at_revision_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); state=enable_state(root); self.assertEqual(state,{"format_version":FORMAT_VERSION,"revision":0,"enabled":True,"tasks":{}}); self.assertEqual(load_state(root),state)
    def test_malformed_json_is_preserved_and_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); d=root/'.praxis'; d.mkdir(); p=d/'state.json'; original=b'{not-json\n'; p.write_bytes(original)
            with self.assertRaises(MalformedStateError): load_state(root)
            with self.assertRaises(MalformedStateError): enable_state(root)
            self.assertEqual(p.read_bytes(),original)
    def test_invalid_schema_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); d=root/'.praxis'; d.mkdir(); (d/'state.json').write_text(json.dumps({"format_version":1,"revision":-1,"enabled":True,"tasks":{}}))
            with self.assertRaises(InvalidStateError): load_state(root)
    def test_unsupported_format_is_preserved_and_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); d=root/'.praxis'; d.mkdir(); p=d/'state.json'; original=json.dumps({"format_version":2,"revision":0,"enabled":True,"tasks":{}}); p.write_text(original)
            with self.assertRaises(UnsupportedFormatError): enable_state(root)
            self.assertEqual(p.read_text(),original)
    def test_reenable_paused_state_requires_matching_revision_and_preserves_unknown_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); d=root/'.praxis'; d.mkdir(); p=d/'state.json'; p.write_text(json.dumps({"format_version":1,"revision":4,"enabled":False,"tasks":{"task_x":{"status":"active"}},"future_metadata":{"keep":True}}))
            with self.assertRaises(RevisionConflictError): enable_state(root)
            updated=enable_state(root,expected_revision=4); self.assertTrue(updated['enabled']); self.assertEqual(updated['revision'],5); self.assertEqual(updated['future_metadata'],{"keep":True})

class StateMutationTests(unittest.TestCase):
    def test_stale_revision_conflict_preserves_newer_state_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); enable_state(root); first=mutate_state(root,0,lambda s:{**s,"marker":"new"}); self.assertEqual(first['revision'],1); p=root/'.praxis'/'state.json'; before=p.read_bytes()
            with self.assertRaises(RevisionConflictError): mutate_state(root,0,lambda s:{**s,"marker":"stale"})
            self.assertEqual(p.read_bytes(),before)
    def test_pause_preserves_tasks_and_unknown_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); enable_state(root); enriched=mutate_state(root,0,lambda s:{**s,"tasks":{"task_a":{"status":"active","pending_choices":["db"]}},"future_metadata":{"keep":True}}); paused=pause_state(root,enriched['revision']); self.assertFalse(paused['enabled']); self.assertEqual(paused['revision'],2); self.assertEqual(paused['tasks'],enriched['tasks']); self.assertEqual(paused['future_metadata'],{"keep":True})
    def test_successful_mutation_increments_revision_exactly_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); enable_state(root); updated=mutate_state(root,0,lambda s:{**s,"marker":1}); self.assertEqual(updated['revision'],1); self.assertEqual(load_state(root)['revision'],1)
    def test_replace_failure_preserves_previous_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); enable_state(root); p=root/'.praxis'/'state.json'; before=p.read_bytes()
            with patch('praxis.state.os.replace',side_effect=OSError('boom')):
                with self.assertRaises(StateWriteError): mutate_state(root,0,lambda s:{**s,"marker":"never"})
            self.assertEqual(p.read_bytes(),before); self.assertEqual(load_state(root)['revision'],0)
