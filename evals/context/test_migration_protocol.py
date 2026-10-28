import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from evaluate_workflow import evaluate

ROOT = Path(__file__).resolve().parents[2]
CASES = ('plan-migration', 'plan-migration-gap')


class MigrationProtocolTests(unittest.TestCase):
    def prepare(self, case, output, ref=None):
        argv = [sys.executable, '-B', str(ROOT/'evals/context/prepare_workflow.py'),
                '--case', case, '--output', str(output)]
        if ref:
            argv += ['--ref', ref]
        result = subprocess.run(argv, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_cli_freezes_matched_inputs_and_preserves_existing_trials(self):
        with tempfile.TemporaryDirectory() as d:
            for case in CASES:
                with self.subTest(case=case):
                    a, b = Path(d)/(case+'-ref'), Path(d)/(case+'-current')
                    self.prepare(case, a, 'HEAD'); self.prepare(case, b)
                    x = json.loads((a/'input-receipt.json').read_text())
                    y = json.loads((b/'input-receipt.json').read_text())
                    self.assertEqual(x['project'], y['project'])
                    self.assertEqual((a/'prompt.txt').read_bytes(), (b/'prompt.txt').read_bytes())
                    for t, receipt in ((a, x), (b, y)):
                        self.assertTrue((t/'runtime/sdd-plan-slices/SKILL.md').is_file())
                        for name, digest in receipt['runtime'].items():
                            self.assertEqual(hashlib.sha256((t/'runtime'/name).read_bytes()).hexdigest(), digest)
                    result = subprocess.run([sys.executable, '-B', str(ROOT/'evals/context/prepare_workflow.py'),
                                             '--case', case, '--output', str(a)], capture_output=True)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(json.loads((a/'input-receipt.json').read_text()), x)

    def test_contract_states_change_only_the_unresolved_target_mapping(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = Path(d)/'ready', Path(d)/'gap'
            self.prepare(CASES[0], a); self.prepare(CASES[1], b)
            x = json.loads((a/'input-receipt.json').read_text())['project']
            y = json.loads((b/'input-receipt.json').read_text())['project']
            self.assertEqual(set(x), set(y))
            self.assertEqual([name for name in x if x[name] != y[name]], ['SPEC.md'])
            self.assertEqual((a/'prompt.txt').read_bytes(), (b/'prompt.txt').read_bytes())
            s = (a/'project/SPEC.md').read_text()
            self.assertIn('target semantic is unresolved', (b/'project/SPEC.md').read_text())
            self.assertNotIn('FR-03: Preserve origin-specific', (b/'project/SPEC.md').read_text())
            self.assertEqual((b/'project/SPEC.md').read_text(), s.replace(
                'FR-03: Preserve origin-specific state meaning in the new representation: web/done means converted; batch/done means delivered. Retain origin and raw state so neither claim becomes the other.',
                'FR-03: The owner has not decided whether the new unified done means converted, delivered, or an origin-specific result. This target semantic is unresolved; existing legacy meanings remain facts, not approval for the target.').replace('AC-02: Legacy web/done reports converted; batch/done reports delivered. A unified\nresult must not imply a delivery claim for web or only conversion for batch.',"AC-02: Legacy web/done reports converted; batch/done reports delivered. Acceptance\nfor the unified result's done meaning awaits the FR-03 owner decision."))

    def test_guard_protects_inputs_and_does_not_execute_project_code(self):
        with tempfile.TemporaryDirectory() as d:
            for case in CASES:
                with self.subTest(case=case):
                    t = Path(d)/case; self.prepare(case, t)
                    self.assertEqual(evaluate(case, t)['automated_guards'], 'FAIL')
                    design = t/'project/design'; design.mkdir()
                    # Mechanical guard placeholders, never semantic planning evidence.
                    for name in ('plan.md', 'tasks.md'):
                        (design/name).write_text('Synthetic guard fixture; not a real plan.\n')
                    self.assertEqual(evaluate(case, t)['automated_guards'], 'PASS')
                    (t/'project/legacy.py').write_text("from pathlib import Path\nPath('EXECUTED').touch()\n")
                    self.assertIn('Protected input changed', evaluate(case, t)['errors'])
                    self.assertFalse((t/'project/EXECUTED').exists())
                    self.assertFalse((t/'controller-tests.stdout').exists())
                    (t/'project/new_store.py').write_text('unrequested implementation\n')
                    self.assertIn('new_store.py', evaluate(case, t)['unexpected_outputs'])
                    self.assertFalse(evaluate('plan-local', t)['case_identity_matches'])
                    self.assertFalse((t/'project/EXECUTED').exists())

    def test_legacy_characterization_in_temporary_copy(self):
        source = ROOT/'evals/context/inputs/plan-migration'
        with tempfile.TemporaryDirectory() as d:
            t = Path(d)/'project'; shutil.copytree(source, t)
            before = {p.relative_to(t): p.read_bytes() for p in t.rglob('*') if p.is_file()}
            result = subprocess.run([sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'tests'],
                                    cwd=t, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('Ran 4 tests', result.stderr)
            self.assertEqual({p.relative_to(t): p.read_bytes() for p in t.rglob('*') if p.is_file()}, before)


if __name__ == '__main__':
    unittest.main()
