import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from evaluate_workflow import evaluate

ROOT = Path(__file__).resolve().parents[2]
CASES = ('verification-profile', 'verification-profile-gap')


class ProfileProtocolTests(unittest.TestCase):
    def prepare(self, case, output, ref=None):
        argv = [sys.executable, '-B', str(ROOT/'evals/context/prepare_workflow.py'),
                '--case', case, '--output', str(output)]
        if ref:
            argv += ['--ref', ref]
        result = subprocess.run(argv, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_public_cli_freezes_inputs_runtime_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            for case in CASES:
                with self.subTest(case=case):
                    a, b = Path(d)/(case+'-ref'), Path(d)/(case+'-current')
                    self.prepare(case, a, 'HEAD'); self.prepare(case, b)
                    x = json.loads((a/'input-receipt.json').read_text())
                    y = json.loads((b/'input-receipt.json').read_text())
                    self.assertEqual(x['project'], y['project'])
                    self.assertEqual((a/'prompt.txt').read_bytes(), (b/'prompt.txt').read_bytes())
                    for trial, receipt in ((a, x), (b, y)):
                        self.assertTrue((trial/'runtime/sdd-verification-design/SKILL.md').is_file())
                        for name, digest in receipt['runtime'].items():
                            self.assertEqual(hashlib.sha256((trial/'runtime'/name).read_bytes()).hexdigest(), digest)
                    result = subprocess.run([sys.executable, '-B', str(ROOT/'evals/context/prepare_workflow.py'),
                                             '--case', case, '--output', str(a)], capture_output=True)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(json.loads((a/'input-receipt.json').read_text()), x)

    def test_states_change_only_adjudication_authority(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = Path(d)/'owned', Path(d)/'gap'
            self.prepare(CASES[0], a); self.prepare(CASES[1], b)
            x = json.loads((a/'input-receipt.json').read_text())['project']
            y = json.loads((b/'input-receipt.json').read_text())['project']
            self.assertEqual(set(x), set(y))
            self.assertEqual([name for name in x if x[name] != y[name]], ['DOMAIN.md'])
            self.assertEqual((a/'prompt.txt').read_bytes(), (b/'prompt.txt').read_bytes())
            self.assertEqual((b/'project/DOMAIN.md').read_text(), (a/'project/DOMAIN.md').read_text().replace(
                'ADJUDICATION: Synthetic domain owner D resolves reviewer disagreements against DOMAIN revision2; unresolved items block semantic acceptance and are reported separately.',
                'ADJUDICATION: No adjudication authority or unresolved-item acceptance policy has been approved. Reviewer disagreement remains open; do not appoint an owner or decide a gate for the owner.'))

    def test_guard_requires_output_and_rejects_implementation_without_execution(self):
        with tempfile.TemporaryDirectory() as d:
            for case in CASES:
                with self.subTest(case=case):
                    trial = Path(d)/case
                    self.prepare(case, trial)
                    self.assertEqual(evaluate(case, trial)['automated_guards'], 'FAIL')
                    report = trial/'project/VERIFICATION.md'
                    report.write_text(' \n')
                    self.assertEqual(evaluate(case, trial)['automated_guards'], 'FAIL')
                    report.write_text('Placeholder tests only the mechanical output/protection guard.\n')
                    self.assertEqual(evaluate(case, trial)['automated_guards'], 'PASS')
                    protected = trial/'project/SPEC.md'; original = protected.read_bytes()
                    protected.write_bytes(original+b'\nunauthorized\n')
                    self.assertEqual(evaluate(case, trial)['automated_guards'], 'FAIL')
                    protected.write_bytes(original)
                    code = trial/'project/service.py'
                    code.write_text("raise RuntimeError('Design guard must not import project code')\n")
                    result = evaluate(case, trial)
                    self.assertEqual(result['automated_guards'], 'FAIL')
                    self.assertIn('service.py', result['unexpected_outputs'])
                    wrong = evaluate('direct', trial)
                    self.assertFalse(wrong['case_identity_matches'])
                    self.assertEqual(wrong['independent_behavior_checks'], [])
                    self.assertFalse((trial/'controller-tests.stdout').exists())
                    code.unlink()
                    self.assertEqual(evaluate(case, trial)['automated_guards'], 'PASS')
                    self.assertEqual(protected.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
