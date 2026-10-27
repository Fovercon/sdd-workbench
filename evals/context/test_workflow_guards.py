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
    def test_probe_rejects_replacing_input_objects_and_whitespace_normalization(self):
        wrong = [
            "def select(items,key):\n items[:] = [dict(x) for x in items]\n return [x for x in items if x['id']==key]\n",
            "def select(items,key):\n return [x for x in items if x['id'].rstrip()==key]\n",
            "def select(items,key):\n return [x for x in items if x['id']==key.strip()]\n",
        ]
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'service.py'
            for code in wrong:
                with self.subTest(code=code):
                    p.write_text(code)
                    with self.assertRaises(AssertionError):probe_selection(p)
