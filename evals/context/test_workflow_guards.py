from pathlib import Path
import tempfile,unittest
from evaluate_workflow import probe_selection

class WorkflowGuardTests(unittest.TestCase):
    def test_probe_rejects_original_substring_bug_and_accepts_exact_selection(self):
        with tempfile.TemporaryDirectory()as d:
            p=Path(d)/'service.py';p.write_text("def select(items,key):\n return [x for x in items if key in x['id']]\n",encoding='utf-8')
            with self.assertRaises(AssertionError):probe_selection(p)
            p.write_text("def select(items,key):\n return [x for x in items if key == x['id']]\n",encoding='utf-8')
            self.assertEqual(len(probe_selection(p)),6)
    def test_probe_rejects_copying_instead_of_preserving_objects(self):
        with tempfile.TemporaryDirectory()as d:
            p=Path(d)/'service.py';p.write_text("def select(items,key):\n return [dict(x) for x in items if key == x['id']]\n",encoding='utf-8')
            with self.assertRaises(AssertionError):probe_selection(p)
