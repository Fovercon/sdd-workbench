import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from evaluate_workflow import evaluate

ROOT = Path(__file__).resolve().parents[2]


class PlanningProtocolTests(unittest.TestCase):
    def prepare(self, case, output, ref=None):
        command = [sys.executable, '-B', str(ROOT/'evals/context/prepare_workflow.py'),
                   '--case', case, '--output', str(output)]
        if ref:
            command += ['--ref', ref]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_public_cli_matched_inputs_for_both_planning_cases(self):
        with tempfile.TemporaryDirectory() as d:
            for case in ('plan-local', 'plan-durable'):
                with self.subTest(case=case):
                    a, b = Path(d)/(case+'-ref'), Path(d)/(case+'-current')
                    self.prepare(case, a, ref='HEAD')
                    self.prepare(case, b)
                    x=json.loads((a/'input-receipt.json').read_text())
                    y=json.loads((b/'input-receipt.json').read_text())
                    self.assertEqual(x['project'], y['project'])
                    self.assertEqual((a/'prompt.txt').read_bytes(), (b/'prompt.txt').read_bytes())
                    self.assertTrue((a/'runtime/sdd-plan-slices/SKILL.md').is_file())
                    self.assertFalse((a/'project/design/plan.md').exists())

    def test_missing_outputs_then_plan_only_outputs_and_source_protection(self):
        with tempfile.TemporaryDirectory() as d:
            for case in ('plan-local', 'plan-durable'):
                with self.subTest(case=case):
                    run=Path(d)/case
                    self.prepare(case, run)
                    self.assertEqual(evaluate(case, run)['automated_guards'], 'FAIL')
                    design=run/'project/design';design.mkdir()
                    (design/'plan.md').write_text('Synthetic plan; semantics require manual review.\n')
                    (design/'tasks.md').write_text('Synthetic slices; not executable authority.\n')
                    self.assertEqual(evaluate(case, run)['automated_guards'], 'PASS')
                    self.assertFalse((run/'controller-tests.stdout').exists())
                    (run/'project/user-notes.txt').write_text('overwritten')
                    self.assertIn('Protected input changed', evaluate(case, run)['errors'])

    def test_planning_rejects_extra_implementation_output(self):
        with tempfile.TemporaryDirectory() as d:
            run=Path(d)/'trial';self.prepare('plan-local', run)
            design=run/'project/design';design.mkdir()
            for name in ('plan.md', 'tasks.md'):
                (design/name).write_text('Synthetic output.\n')
            (run/'project/plugin.py').write_text('unrequested production code\n')
            self.assertIn('plugin.py', evaluate('plan-local', run)['unexpected_outputs'])


if __name__ == '__main__':
    unittest.main()
