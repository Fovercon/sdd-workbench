from pathlib import Path
import json,subprocess,sys,tempfile,unittest
from evaluate_workflow import probe_selection
from prepare_workflow import prepare

class WorkflowGuardTests(unittest.TestCase):
    def run_cli(self, case, run):
        completed = subprocess.run(
            [sys.executable, '-B', str(Path(__file__).with_name('evaluate_workflow.py')), case, str(run)],
            text=True, capture_output=True, check=False)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload, json.loads((run / 'guard-evaluation.json').read_text()))
        return completed.returncode, payload

    def test_cli_missing_report_fails_and_requested_output_passes(self):
        with tempfile.TemporaryDirectory() as base:
            run = prepare('impact-proposed', Path(base) / 'run')
            code, payload = self.run_cli('impact-proposed', run)
            self.assertEqual(payload['automated_guards'], 'FAIL')
            self.assertIn('Impact report missing', payload['errors'])
            self.assertEqual(code, 1, 'shell callers must observe guard failure')
            (run / 'project/IMPACT.md').write_text('Placeholder; guards do not grade report semantics.\n')
            code, payload = self.run_cli('impact-proposed', run)
            self.assertEqual(payload['automated_guards'], 'PASS')
            self.assertEqual(code, 0)

    def test_cli_protected_input_change_is_nonzero(self):
        with tempfile.TemporaryDirectory() as base:
            run = prepare('impact-proposed', Path(base) / 'run')
            (run / 'project/IMPACT.md').write_text('Placeholder; not a semantic certificate.\n')
            (run / 'project/SPEC.md').write_text('unauthorized change\n')
            code, payload = self.run_cli('impact-proposed', run)
            self.assertEqual(payload['automated_guards'], 'FAIL')
            self.assertIn('SPEC.md', payload['protected_changes'])
            self.assertEqual(code, 1)

    def test_cli_wrong_case_fails_before_executing_project_code(self):
        with tempfile.TemporaryDirectory() as base:
            run = prepare('impact-proposed', Path(base) / 'run')
            marker = run / 'project/executed.txt'
            (run / 'project/service.py').write_text(
                'from pathlib import Path\n'
                f'Path({str(marker)!r}).write_text("executed")\n')
            code, payload = self.run_cli('direct', run)
            self.assertEqual(payload['automated_guards'], 'FAIL')
            self.assertFalse(payload['case_identity_matches'])
            self.assertEqual(code, 1)
            self.assertFalse(marker.exists())
            self.assertFalse((run / 'controller-tests.stdout').exists())

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
