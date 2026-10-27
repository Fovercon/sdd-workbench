import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from evaluate_workflow import evaluate

ROOT = Path(__file__).resolve().parents[2]


class ImpactProtocolTests(unittest.TestCase):
    def prepare(self, case, output, ref=None):
        command = [sys.executable, '-B', str(ROOT / 'evals/context/prepare_workflow.py'),
                   '--case', case, '--output', str(output)]
        if ref:
            command += ['--ref', ref]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_ref_and_worktree_preserve_case_inputs_and_historical_receipt(self):
        with tempfile.TemporaryDirectory() as base:
            for case in ('impact-proposed', 'impact-approved'):
                with self.subTest(case=case):
                    a, b = Path(base) / (case + '-ref'), Path(base) / (case + '-current')
                    self.prepare(case, a, 'HEAD'); self.prepare(case, b)
                    x = json.loads((a / 'input-receipt.json').read_text())
                    y = json.loads((b / 'input-receipt.json').read_text())
                    self.assertEqual(x['project'], y['project'])
                    self.assertEqual(x['runtime'], y['runtime'])
                    self.assertEqual((a / 'prompt.txt').read_bytes(), (b / 'prompt.txt').read_bytes())
                    self.assertEqual({p.name for p in (a / 'runtime').iterdir()}, {'sdd-change-impact'})
                    project = a / 'project'
                    old_hash = hashlib.sha256((project / 'archive/SPEC-v1.md').read_bytes()).hexdigest()
                    receipt = json.loads((project / 'TRACE-RECEIPT.json').read_text())
                    self.assertEqual(receipt['sources']['SPEC.md'], old_hash)
                    current_hash = hashlib.sha256((project / 'SPEC.md').read_bytes()).hexdigest()
                    self.assertEqual(current_hash == old_hash, case == 'impact-proposed')

    def test_required_report_only_and_protected_contracts(self):
        with tempfile.TemporaryDirectory() as base:
            for case in ('impact-proposed', 'impact-approved'):
                with self.subTest(case=case):
                    run = Path(base) / case; self.prepare(case, run)
                    self.assertEqual(evaluate(case, run)['automated_guards'], 'FAIL')
                    (run / 'project/IMPACT.md').write_text('Synthetic analysis; not a semantic certificate.\n')
                    self.assertEqual(evaluate(case, run)['automated_guards'], 'PASS')
                    self.assertFalse((run / 'controller-tests.stdout').exists())
                    (run / 'project/SPEC.md').write_text('overwritten')
                    self.assertIn('Protected input changed', evaluate(case, run)['errors'])

    def test_pair_identity_and_unrequested_implementation_are_rejected(self):
        with tempfile.TemporaryDirectory() as base:
            run = Path(base) / 'run'; self.prepare('impact-proposed', run)
            self.assertFalse(evaluate('impact-approved', run)['case_identity_matches'])
            (run / 'project/IMPACT.md').write_text('Synthetic analysis.\n')
            (run / 'project/patch.py').write_text('unrequested implementation\n')
            self.assertIn('patch.py', evaluate('impact-proposed', run)['unexpected_outputs'])


if __name__ == '__main__':
    unittest.main()
